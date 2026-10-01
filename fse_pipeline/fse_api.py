# fse_pipeline/fse_api.py
import os
import re
import sys
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Optional
from fse_pipeline.config import settings

TEST_DATA_DIR = Path(__file__).parent.parent / "tests" / "test_data"
TEST_FLIGHT_LOGS_PATH = TEST_DATA_DIR / "Flight Logs by Reg.csv"
TEST_FLIGHT_LOGS_PATH = TEST_DATA_DIR / "Flight Logs by Reg.csv"
TEST_AIRCRAFT_PATH = TEST_DATA_DIR / "Aircraft By Key.csv"
TEST_STATS_PATH = TEST_DATA_DIR / "Statistics By Key.csv"

BASE_URL = "https://server.fseconomy.net/userctl"

# FBO Data Feeds

def create_test_data_frame():
    script_dir = Path(__file__).resolve().parent.parent
    return pd.read_csv(script_dir / "tests" / "test_data" / "FBOs By Key.csv")

def create_data_frame():
    url = f"https://server.fseconomy.net/data?userkey={settings.fse_user_key}&format=csv&query=fbos&search=key&readaccesskey={settings.fsegroup1}"
    try:
        return pd.read_csv(url)
    except Exception as e:
        print(f"Error getting datafeed: {e}")
        sys.exit(1)

# Aircraft & Statistics Data Feeds

def fetch_aircraft_flight_logs(ac_reg: str, month: str, year: str, test: bool = False) -> pd.DataFrame:
    """Fetches flight log data for a specific aircraft registration."""
    if test:
        try:
            df = pd.read_csv(TEST_FLIGHT_LOGS_PATH)
            if not df.empty:
                filtered_df = df[(df["Type"] == "flight") & (df["Registration"] == ac_reg)] if "Registration" in df.columns else df[df["Type"] == "flight"]
                return filtered_df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error reading test flight log CSV: {e}")
            return pd.DataFrame()

    url = (
        f"https://server.fseconomy.net/data?userkey={settings.fse_user_key}"
        f"&format=csv&query=flightlogs&search=monthyear"
        f"&aircraftreg={ac_reg}&month={month}&year={year}"
    )
    try:
        df = pd.read_csv(url)
        if not df.empty and "Type" in df.columns:
            return df[df["Type"] == "flight"]
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching logs for {ac_reg}: {e}")
        return pd.DataFrame()

def fetch_aircraft_by_key(test: bool = False) -> pd.DataFrame:
    """Fetches aircraft list by key to evaluate fixed monthly costs."""
    if test:
        try:
            return pd.read_csv(TEST_AIRCRAFT_PATH)
        except Exception as e:
            print(f"Error loading test aircraft CSV: {e}")
            return pd.DataFrame()

    url = (
        f"https://server.fseconomy.net/data?userkey={settings.fse_user_key}"
        f"&format=csv&query=aircraft&search=key&readaccesskey={settings.fsegroup2}"
    )
    try:
        return pd.read_csv(url)
    except Exception as e:
        print(f"Error fetching aircraft by key: {e}")
        return pd.DataFrame()

def fetch_statistics_by_key(test: bool = False, target_acc: str = '') -> pd.DataFrame:
    """Fetches group statistics by key to inspect balances."""
    if test:
        try:
            return pd.read_csv(TEST_STATS_PATH)
        except Exception as e:
            print(f"Error loading test statistics CSV: {e}")
            return pd.DataFrame()

    url = (
        f"https://server.fseconomy.net/data?userkey={settings.fse_user_key}"
        f"&format=csv&query=statistics&search=key&readaccesskey={target_acc}"
    )
    try:
        return pd.read_csv(url)
    except Exception as e:
        print(f"Error fetching statistics by key: {e}")
        return pd.DataFrame()

# Web Session & Financial Transfer Functions

def login_fse_session(session: requests.Session, username: Optional[str] = None, password: Optional[str] = None) -> bool:
    """Authenticates the web session against FSE userctl."""
    user = username or settings.fse_username
    pwd = password or settings.fsepassword

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://server.fseconomy.net/index.jsp",
    })

    login_payload = {
        "user": user,
        "password": pwd,
        "event": "Agree & Log in",
    }

    print("🔐 Authenticating FSE session...")
    try:
        response = session.post(BASE_URL, data=login_payload, timeout=10)
        res_text = response.text

        error_match = re.search(
            r'<div\s+class=["\']content error["\']>\s*"?([^<"\n]+)"?',
            res_text,
            re.IGNORECASE,
        )

        if error_match:
            clean_msg = error_match.group(1).strip()
            print(f"❌ Transfer failed [FSE Error]: {clean_msg}")
            return False
        
        if "Log out" not in response.text:
            print("❌ Login failed: Invalid credentials or session rejected.")
            return False
        print("✅ Login successful! Session established.")
        return True
    except Exception as e:
        print(f"❌ Session login request failed: {e}")
        return False

def logout_fse_session(session: requests.Session) -> None:
    """Safely logs out and terminates the FSE web session."""
    print("🔒 Logging out of FSE...")
    try:
        session.get(f"{BASE_URL}?event=Log+out", timeout=5)
    except Exception as e:
        print(f"⚠️ Warning during logout: {e}")
    finally:
        session.close()

def send_fse_bank_transfer(
    session: requests.Session,
    source_id: str,
    target_id: str,
    target_name: str,
    amount: float,
    comment: str,
    test: bool = True,
) -> bool:
    """Executes a bank transfer POST request using an active web session."""
    transfer_amount_val = 1.00 if test else amount
    transfer_amount_str = f"{transfer_amount_val:.2f}"

    transfer_payload = {
        "event": "bankTransfer",
        "returnpage": "/banksummary.jsp",
        "id": source_id,
        "accountname": target_name,
        "account": target_id,
        "comment": comment,
        "amount": transfer_amount_str,
    }

    mode_label = f"[TEST MODE ${transfer_amount_str}]" if test else f"[${transfer_amount_str}]"
    print(f"💸 Executing transfer {mode_label} to '{target_name}' (ID: {target_id})...")

    try:
        response = session.post(BASE_URL, data=transfer_payload, timeout=10)
        res_text = response.text

        if "Not logged in" in res_text or "Session expired" in res_text:
            print("❌ Transfer failed: Session expired or invalid.")
            return False

        error_match = re.search(
            r'<div\s+class=["\']content error["\']>\s*"?([^<"\n]+)"?',
            res_text,
            re.IGNORECASE,
        )

        if error_match:
            clean_msg = error_match.group(1).strip()
            print(f"❌ Transfer failed [FSE Error]: {clean_msg}")
            return False

        print(f"✅ Transfer of ${transfer_amount_str} executed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending bank transfer request: {e}")
        return False

# API and Login Validation checks
class FSEAPIError(Exception):
    """Raised when FSE API credentials or queries are invalid."""
    pass

def _check_single_key_pair(user_key: str, group_key: str, label: str) -> None:
    """Helper to query FSE XML endpoint and raise FSE's exact error message on failure."""
    if not group_key:
        raise FSEAPIError(f"Configuration Error: {label} is missing from environment variables.")

    url = (
        f"https://server.fseconomy.net/data"
        f"?userkey={user_key}"
        f"&format=xml"
        f"&query=statistics"
        f"&search=key"
        f"&readaccesskey={group_key}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.text.strip())

        # If FSE returns an <Error> node, extract and raise its exact text
        if root.tag == "Error":
            fse_message = root.text.strip() if root.text else "Unknown FSE error"
            raise FSEAPIError(f"Validation failed {label} : {fse_message}")

    except ET.ParseError:
        raise FSEAPIError(f"Received malformed XML response while testing {label}.")
    except requests.RequestException as e:
        raise FSEAPIError(f"Network error while validating {label}: {e}")

def validate_all_credentials(user_key: str, group_key_1: str, group_key_2: str, username: str, password: str) -> bool:
    """Validates USER_KEY against both GROUP_KEY_1 and GROUP_KEY_2 on startup."""
    print("Validating FSE API keys against FSEconomy...")

    errors = []

    if not user_key:
        errors.append("Configuration Error: FSE_USER_KEY is missing from environment variables.")

    # Run check for Group 1
    err1 = _check_single_key_pair(user_key, group_key_1, "Group 1 Key")
    if err1:
        errors.append(err1)
    
    # Run check for Group 2
    err2 = _check_single_key_pair(user_key, group_key_2, "Group 2 Key")
    if err2:
        errors.append(err2)

    if errors:
        error_summary = "\n  - ".join(errors)
        raise FSEAPIError(f"Validation failed for the following key(s):\n  - {error_summary}")

    print("All API keys validated successfully!")
    print('Attempting to create logged in session')

    session = requests.Session()
    login_fse_session(session, username, password)
    logout_fse_session(session)

    return True

def test_all_credentials():
    try:
        validate_all_credentials(settings.fse_user_key, settings.fsegroup1, settings.fsegroup2, settings.fse_username, settings.fsepassword)
    except FSEAPIError as err:
        print(f"CRITICAL STARTUP FAILURE:\n{err}")
        return