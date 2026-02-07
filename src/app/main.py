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

Configuration required in file 'config.py'

"""

import pandas as pd
import sys
import schedule
import time
import datetime
import warnings
import os

from discord import SyncWebhook, Embed
from pathlib import Path

from config import supplies_threshold, jet_threshold, avgas_threshold
fbohook_url = os.environ.get('FBOHOOK', 'Not Set')
mxhook_url = os.environ.get('MXHOOK', 'Not Set')
fseuser = os.environ.get('FSEUSER', 'Not Set')
fsegroup1 = os.environ.get('FSEGROUP1', 'Not Set')
fsegroup2 = os.environ.get('FSEGROUP2', 'Not Set')
aircraft = os.environ.get('AIRCRAFT', 'Not Set')


warnings.filterwarnings("ignore")

'''----------------------- FSE FBO Script ---------------------------'''

# Create dataframe from CSV datafeeds
def create_data_frame(url1 : str, url2 : str):
    """Creates a dataframe from the FSE FBO by Key datafeed.
    
    Retreives two instances of the FSE FBO datafeeds, combines them into a single dataframe.

    Args:
        url1: The FSE datafeed URL for the first group csv table to be downloaded.
        url2: The FSE datafeed URL for the second group csv table to be downloaded.
    
    Returns:
        A single dataframe of the combined FSE datafeeds.

    Raises:
        Exception: An error occoured resulting in one or both of the FSE datafeeds not being accessed.
    """
    try:
        df1 = pd.read_csv(url1)
        df2 = pd.read_csv(url2)
        df = pd.concat([df1, df2], ignore_index=True)
    except:
        print("error getting datafeed")
        # logger.info("\nAn error occoured fetching datafeeds")
        fbo_send_message("\nAn error occoured fetching datafeeds")
        sys.exit(1)
    return df

# test dataframes using local csv files
def create_test_data_frame():
    """Creates a test dataframe from stored csv files.
    
    Loads the two test files, fbo.csv & fbo1.csv, instead of accessing the FSE datafeed system.
  
    Returns:
        A single dataframe of the combined test FSE datafeeds .csv's.
    """
    script_dir = Path(__file__).resolve().parent
    print(f'{script_dir}/fbos.csv')
    df1 = pd.read_csv(f'{script_dir}/tests/fbos.csv')
    df2 = pd.read_csv(f'{script_dir}/tests/fbos1.csv')
    df = pd.concat([df1, df2], ignore_index=True)
    return df

# Webhook output to Discord
def fbo_send_message(title_str, message_str):
    """Sends an embed webhook element to the designated discord server.
    
    Args:
        title_str: The title to be used in the embeded discord element.
        message_str: The description to be used in the embeded discord element.
    """
    print(f'{title_str} : {message_str}')
    webhook = SyncWebhook.from_url(fbohook_url)
    webhook.send(embed=Embed(title = title_str, description = message_str))

# Main FBO checks Functions

def fbo_supply_warning(df):
    """Checks for FBOs that might need supplies
    
    Checks FBO listings to isolate airports which have a supplied day value below the threshold preset in config.
    Generates the Title and Body text for the discord message, and passes them to the fbo_send_message function.

    Args:
        df: The main dataframe of FBO listings.

    Raises:
        KeyError: An error occoured resulting in no data to sort.
    
    """
    # Check for airport closure warning
    try:
        df.loc[df["SuppliedDays"] < supplies_threshold, "Warning"] = "True"
    except KeyError:
        print("error getting datafeed")
        # logger.info("\nAn error occoured fetching datafeeds")
        fbo_send_message("\nAn error occoured fetching datafeeds")
        sys.exit(1)

    airport_warning = df.loc[df["Warning"] == "True"]
    airport_warning.shape
    if airport_warning.empty:
        title_str = "FSE FBO Update"
        message_str = "No Airport Supply Warnings"
        
    else:
        title_str = "FSE FBO Update"
        message_str = "Airports with supply warnings:\n {}".format(
            airport_warning[["Airport", "SuppliedDays"]].to_string(index=False)
        )
    # logger.info("\n{}".format(message_str))
    fbo_send_message(title_str, message_str)

def fbo_jetA_warning(df):
    """Checks for FBOs that might need Jet-A Orders
    
    Checks FBO listings to isolate airports which have Jet-A value below the threshold preset in config.
    Removes airports from the list which do not sell Jet-A.
    Generates the Title and Body text for the discord message, and passes them to the fbo_send_message function.

    Args:
        df: The main dataframe of FBO listings.

    Raises:
        KeyError: An error occoured resulting in no data to sort.
    
    """
    try:
        df.loc[df["FuelJetA"] < jet_threshold, "OrderJet"] = "True"
        df.loc[df["PriceJetAGal"] == 0, "OrderJet"] = ""
    except KeyError:
        print("error getting datafeed")
        sys.exit(1)

    jeta_resupply = df.loc[df["OrderJet"] == "True"]
    jeta_resupply.shape
    if jeta_resupply.empty:
        title_str = "No JetA Orders Requried"
        message_str = ""
    else:
        title_str = "Airports requiring JetA Orders:"
        message_str = "{}".format(
            jeta_resupply[["Airport", "FuelJetA"]].to_string(index=False)
        )
    # logger.info("\n{}".format(message_str))
    fbo_send_message(title_str, message_str)

def fbo_avgas_warning(df):
    """Checks for FBOs that might need Avgas Orders
    
    Checks FBO listings to isolate airports which have Avgas value below the threshold preset in config.
    Removes airports from the list which do not sell Avgas.
    Generates the Title and Body text for the discord message, and passes them to the fbo_send_message function.

    Args:
        df: The main dataframe of FBO listings.

    Raises:
        KeyError: An error occoured resulting in no data to sort.
    
    """
    try:
        df.loc[df["Fuel100LL"] < avgas_threshold, "OrderAvgas"] = "True"
        df.loc[df["Price100LLGal"] == 0, "OrderAvgas"] = ""
    except KeyError:
        print("error getting datafeed")
        sys.exit(1)

    avgas_resupply = df.loc[df["OrderAvgas"] == "True"]
    avgas_resupply.shape
    if avgas_resupply.empty:
        title_str = "No Avgas Orders Required"
        message_str = ""
    else:
        title_str = "Airports requiring Avgas Orders:"
        message_str = "{}".format(
            avgas_resupply[["Airport", "Fuel100LL"]].to_string(index=False)
        )
    # logger.info("\n{}".format(message_str))
    fbo_send_message(title_str, message_str)

def main_fbo(test: bool = False):
    """Script entry point.
    
    Generates the two URL's to be used to collect the datafeed from FSE.
    Runs the FBO Supplies, Jet-A and Avgas Warnings.   

    Args:
        test: If True will generate the datafeed from the two test .csv files. False will pull live datafeeds from FSE.
                Defaults to False
    """
    print('Running FBO Script')
    dataurl1 = f"https://server.fseconomy.net/data?userkey={fseuser}&format=csv&query=fbos&search=key&readaccesskey={fsegroup1}"
    dataurl2 = f"https://server.fseconomy.net/data?userkey={fseuser}&format=csv&query=fbos&search=key&readaccesskey={fsegroup2}"
    if test:
        df = create_test_data_frame()
        print("Test mode: Using CSV data")
    else:
        df = create_data_frame(dataurl1, dataurl2)
    fbo_supply_warning(df)
    fbo_jetA_warning(df)
    fbo_avgas_warning(df)

'''------------------------- MX Monthly Script ----------------------------'''
# create dataframe from CSV datafeeds
def calcTargetDate():
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    target_month = last_month.strftime("%m")
    target_year = last_month.strftime("%Y")
    return target_month, target_year

def createurl():
    target_month, target_year = calcTargetDate()
    url =  f"https://server.fseconomy.net/data?userkey={fseuser}&format=csv&query=flightlogs&search=monthyear&readaccesskey={fseuser}&month={target_month}&year={target_year}"
    return url

def convertdec(time_str):
    hours, minutes = map(int, time_str.split(":"))
    decimal_time = round((hours + (minutes / 60)), 1)
    return decimal_time

def createdataframe(url):
    try:
        df = pd.read_csv(url)
        #trim dataframe to only flights
        df = df[((df.Type == 'flight'))]
    except:
        print("Error gettting datafeed")
        sys.exit(1)
    return df

def CalculateAircraftCost(df, rego, cost):
    df1 = df.query("Aircraft == @rego")
    df1['DecTime'] = df1['FlightTime'].apply(convertdec)
    TotalHrs = round(df1['DecTime'].sum(), 1)
    TotalCost = format(round(TotalHrs * cost, 2), '.2f')
    title_str = f'Monthly totals for {rego}:'
    message_str = f'{TotalHrs} Hours at ${cost} = ${TotalCost}'
    mx_send_message(title_str, message_str)
    

# Webhook output to Discord
def mx_send_message(title_str, message_str):
    """Sends an embed webhook element to the designated discord server.
    
    Args:
        title_str: The title to be used in the embeded discord element.
        message_str: The description to be used in the embeded discord element.
    """
    print(f'{title_str} : {message_str}')
    webhook = SyncWebhook.from_url(mxhook_url)
    webhook.send(embed=Embed(title = title_str, description = message_str))
    
def mxmain():
    if datetime.date.today().day != 1:
        return
    
    url = createurl()
    df = createdataframe(url)
    for airframe, rate in aircraft.items():
        CalculateAircraftCost(df, airframe, rate)


# Task scheduling - Times in UTC for Docker
def run_check():
    print(f'{datetime.datetime.now()} fse-bot still running')

schedule.every().day.at("20:00").do(main_fbo)
schedule.every().day.at("09:00").do(main_fbo)
schedule.every().day.at("20:00").do(mxmain)
schedule.every().hour.at(":00").do(run_check)

if __name__ == "__main__":
    print('Starting FSE-Bot Schedule')
    while True:
        schedule.run_pending()
        time.sleep(1)
