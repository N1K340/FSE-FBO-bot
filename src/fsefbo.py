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

Configuration required in file 'fsefboconfig.py'

"""

import logging
import os
import sys

import pandas as pd

from discord import SyncWebhook, Embed
from pathlib import Path

from fsefboconfigreal import fbohook_url, supplies_threshold, jet_threshold, avgas_threshold, fseuser, fsegroup1, fsegroup2


# setup the logger
logger = logging.getLogger(__name__)
if not os.path.exists(f"{os.path.dirname(__file__)}/logs/"):
    os.makedirs(f"{os.path.dirname(__file__)}/logs/")
logging.basicConfig(
    filename=f"{os.path.dirname(__file__)}/logs/fsefbo.log",
    format="%(asctime)s:%(message)s",
    level=logging.INFO
)

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
        logger.info("\nAn error occoured fetching datafeeds")
        send_message("\nAn error occoured fetching datafeeds")
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
def send_message(title_str, message_str):
    """Sends an embed webhook element to the designated discord server.
    
    Args:
        title_str: The title to be used in the embeded discord element.
        message_str: The description to be used in the embeded discord element.
    """
    webhook = SyncWebhook.from_url(fbohook_url)
    webhook.send(embed = Embed(title = title_str, description = message_str))

# Main FBO checks Functions

def fbo_supply_warning(df):
    """Checks for FBOs that might need supplies
    
    Checks FBO listings to isolate airports which have a supplied day value below the threshold preset in config.
    Generates the Title and Body text for the discord message, and passes them to the send_message function.

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
        logger.info("\nAn error occoured fetching datafeeds")
        send_message("\nAn error occoured fetching datafeeds")
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
    logger.info("\n{}".format(message_str))
    send_message(title_str, message_str)

def fbo_jetA_warning(df):
    """Checks for FBOs that might need Jet-A Orders
    
    Checks FBO listings to isolate airports which have Jet-A value below the threshold preset in config.
    Removes airports from the list which do not sell Jet-A.
    Generates the Title and Body text for the discord message, and passes them to the send_message function.

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
    logger.info("\n{}".format(message_str))
    send_message(title_str, message_str)

def fbo_avgas_warning(df):
    """Checks for FBOs that might need Avgas Orders
    
    Checks FBO listings to isolate airports which have Avgas value below the threshold preset in config.
    Removes airports from the list which do not sell Avgas.
    Generates the Title and Body text for the discord message, and passes them to the send_message function.

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
    logger.info("\n{}".format(message_str))
    send_message(title_str, message_str)

def main(test: bool = False):
    """Script entry point.
    
    Generates the two URL's to be used to collect the datafeed from FSE.
    Runs the FBO Supplies, Jet-A and Avgas Warnings.   

    Args:
        test: If True will generate the datafeed from the two test .csv files. False will pull live datafeeds from FSE.
                Defaults to False
    """
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


if __name__ == "__main__":
    main()