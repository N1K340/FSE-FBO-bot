#!/usr/bin/env python3.9

"""
Python script to monitor FSE FBO operations

- Check FBO has more than X days of supplies on hand
- Check FBO which sells JetA has minimum amount on hand (Fuel price > $1)
- Check FBO which sells Avgas has minimum amount on hand (Fuel price > $1)
- Output results to JSON for a discord bot to disseminate
- Output results to '../logs/fsefbo.log'

v1.1
- Output results as a discord embeded webhook
- Refactored code

v2.0
- Refactored to use schedule library to run as a docker app
- merged multiple functions to create standalone FSE app
- functions split out to modules

v2.1
- Removed hard coded aircraft dictionary in favour of environment variable for easier changes

v3.0
- Complete refactor of code
- split functions into package
- added funds transfer capabilities

Configuration required in file 'config.py'
"""

import schedule
import datetime
import time
import requests

from fse_pipeline.config import settings
from fse_pipeline import fse_api, analytics, reporters, notifications, __version__

# FBO Daily Check

def daily_fbo_check(test: bool = False):
    start_total = time.time()
    print("Running FBO Monitoring Check...")

    # 1. Measure API / Data Fetching
    try:
        df = fse_api.create_test_data_frame() if test else fse_api.create_data_frame()
    except Exception as e:
        print(f"Error getting datafeed: {e}")
        return

    # 2. Measure Analytics processing
    low_supplies = analytics.get_supply_warnings(df)
    low_jeta = analytics.get_jeta_warnings(df)
    low_avgas = analytics.get_avgas_warnings(df)

    # 3. Measure Report Building
    report_embed = reporters.build_combined_fbo_embed(low_supplies, low_jeta, low_avgas, test=test)

    # 4. Measure Discord Webhook Network Call
    notifications.send_fbo_embed(report_embed)

# Monthly Maint Calcs

def run_mx_monthly(test: bool = False):
    """Runs month-end operations checks for aircraft maintenance/lease and executes financial transfers."""
    if not test and datetime.date.today().day != 1:
        print("Skipping monthly MX check (only runs on the 1st of the month).")
        return

    print("Running Monthly Aircraft Lease & Transfer Pipeline...")
    month, year = analytics.calc_target_date()

    # Step 1: Calculate aircraft usage and lease costs
    aircraft_summary = []
    total_lease_cost = 0.0

    for ac_reg, rate in settings.aircraft.items():
        df = fse_api.fetch_aircraft_flight_logs(ac_reg, month, year, test=test)
        hrs, cost = analytics.calculate_aircraft_lease_cost(df, rate)
        total_lease_cost += cost
        aircraft_summary.append({
            "rego": ac_reg,
            "hours": hrs,
            "rate": rate,
            "cost": cost
        })

    # Step 2: Determine total monthly obligations (Monthly Fees + Step 1 Leases + Buffer)
    ac_key_df = fse_api.fetch_aircraft_by_key(test=test)
    monthly_ac_costs = analytics.calculate_monthly_aircraft_fees(ac_key_df)
    buffer_cost = settings.monthly_buffer
    total_obligations = total_lease_cost + monthly_ac_costs + buffer_cost

    # Step 3: Verify Account B balance and execute cash transfers
    stats_df = fse_api.fetch_statistics_by_key(test=test, target_acc=settings.fsegroup2)
    aircraft_account_balance = analytics.get_account_balance(stats_df)

    session = requests.Session()
    transfer_status = "Success"
    transfer_notes = ""

    try:
        # 3a. Check if Account B needs funds from Account A
        if aircraft_account_balance < total_obligations:
            shortfall = total_obligations - aircraft_account_balance
            print(f"Insufficient funds in Account B. Shortfall: ${shortfall:,.2f}. Attempting transfer from Account A...")

            if not fse_api.login_fse_session(session):
                transfer_status = "Failed"
                transfer_notes = "Failed to authenticate web session for Account A -> Account B transfer."
                embed = reporters.build_monthly_mx_embed(
                    aircraft_summary, month, year, monthly_ac_costs, buffer_cost, aircraft_account_balance, transfer_status, transfer_notes, test=test
                )
                notifications.send_mx_embed(embed)
                return

            transfer_a_to_b = fse_api.send_fse_bank_transfer(
                session=session,
                source_id=settings.PERSONAL_ACC_ID,
                target_id=settings.AIRCRAFT_ACC_ID,
                target_name=settings.AIRCRAFT_ACC_NAME,
                amount=shortfall,
                comment=f"Monthly obligations top-up ({month}/{year})",
                test=test
            )

            if not transfer_a_to_b:
                transfer_status = "Failed"
                transfer_notes = f"Transfer of ${shortfall:,.2f} from Account A to Account B failed."
                embed = reporters.build_monthly_mx_embed(
                    aircraft_summary, month, year, monthly_ac_costs, buffer_cost, aircraft_account_balance, transfer_status, transfer_notes, test=test
                )
                notifications.send_mx_embed(embed)
                return

            transfer_notes += f"Transferred ${shortfall:,.2f} from Account A to Account B. "
            aircraft_account_balance += shortfall

        # 3b. Transfer lease fees from Account B to Account C
        if total_lease_cost > 0:
            if not session.headers.get("Referer"):
                if not fse_api.login_fse_session(session):
                    transfer_status = "Failed"
                    transfer_notes += "Failed to authenticate web session for Account B -> Account C lease transfer."
                    embed = reporters.build_monthly_mx_embed(
                        aircraft_summary, month, year, monthly_ac_costs, buffer_cost, aircraft_account_balance, transfer_status, transfer_notes, test=test
                    )
                    notifications.send_mx_embed(embed)
                    return

            transfer_b_to_c = fse_api.send_fse_bank_transfer(
                session=session,
                source_id=settings.AIRCRAFT_ACC_ID,
                target_id=settings.MAINT_ACC_ID,
                target_name=settings.MAINT_ACC_NAME,
                amount=total_lease_cost,
                comment=f"Monthly aircraft lease payment ({month}/{year})",
                test=test
            )

            if not transfer_b_to_c:
                transfer_status = "Failed"
                transfer_notes += f"Transfer of ${total_lease_cost:,.2f} lease fees from Account B to Account C failed."
                embed = reporters.build_monthly_mx_embed(
                    aircraft_summary, month, year, monthly_ac_costs, buffer_cost, aircraft_account_balance, transfer_status, transfer_notes, test=test
                )
                notifications.send_mx_embed(embed)
                return
            
            aircraft_account_balance -= total_lease_cost if not test else 1.00
            transfer_notes += f"Transferred ${total_lease_cost:,.2f} lease fees from Account B to Account C."

    finally:
        fse_api.logout_fse_session(session)

    embed = reporters.build_monthly_mx_embed(
        aircraft_summary, month, year, monthly_ac_costs, buffer_cost, aircraft_account_balance, transfer_status, transfer_notes, test=test
    )

    if test:
        print(f"Test Mode Embed output:\nTitle: {embed.title}\nFields: {embed.fields}")
    
    notifications.send_mx_embed(embed)

def run_heartbeat():
    """Once an hour sends a message to terminal to confirm operating"""
    print(f'{datetime.datetime.now()} fse-bot still running {__version__}')

# Task scheduling - Times in UTC for Docker
schedule.every().hour.at(":00").do(run_heartbeat)
schedule.every().day.at("20:00").do(daily_fbo_check)
schedule.every().day.at("09:00").do(daily_fbo_check)

if __name__ == "__main__":
    if not settings.TEST_MODE:
        print(f'Starting FSE-Bot Schedule {__version__}')
        run_heartbeat()
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        print(f'Starting FSE-Bot Schedule {__version__}')
        if settings.TEST_MODE:
            print(f'TEST MODE ENABLED')
        daily_fbo_check(settings.TEST_MODE)
        run_mx_monthly(settings.TEST_MODE)