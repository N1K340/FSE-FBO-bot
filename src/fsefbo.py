#!/usr/bin/env python3.9

"""
Python script to monitor FSE FBO operations
- Check FBO has more than X days of supplies on hand
- Check FBO which sells JetA has minimum ammount on hand (Fuel price > $1)
- Check FBO which sells Avgas has minimum ammount on hand (Fuel price > $1)
- Output results to JSON for a discord bot to diseminate
- Output results to '../logs/fsefbo.log'

Configuration required in file 'fsefboconfig.py'

"""


import pandas as pd
import logging
import json
import sys
import os
import fsefboconfig as cfg
from pathlib import Path

# setup the logger
logger = logging.getLogger(__name__)
if not os.path.exists(f"{os.path.dirname(__file__)}/logs/"):
    os.makedirs(f"{os.path.dirname(__file__)}/logs/")
logging.basicConfig(
    filename=f"{os.path.dirname(__file__)}/logs/fsefbo.log",
    format="%(asctime)s:%(message)s",
    level=logging.INFO
)

# Variables
script_dir = Path(__file__).resolve().parent
url1 = f"https://server.fseconomy.net/data?userkey={cfg.fseuser}&format=csv&query=fbos&search=key&readaccesskey={cfg.fsegroup1}"
url2 = f"https://server.fseconomy.net/data?userkey={cfg.fseuser}&format=csv&query=fbos&search=key&readaccesskey={cfg.fsegroup2}"
imp_var = [
    "Airport",
    "FuelJetA",
    "PriceJetAGal",
    "Fuel100LL",
    "Price100LLGal",
    "SuppliedDays",
]

# Create dataframe from CSV datafeeds
# Main entry point
"""def createdataframe():
    try:
        df1 = pd.read_csv(url1)
        df2 = pd.read_csv(url2)
        df = pd.concat([df1, df2], ignore_index=True)
    except:
        print("error getting datafeed")
        logger.info("\nAn error occoured fetching datafeeds")
        send_message("\nAn error occoured fetching datafeeds")
        sys.exit(1)
    fbochecks(df)"""

# test dataframes using local csv files
def createdataframe():
    print(f'{script_dir}/fbos.csv')
    df1 = pd.read_csv(f'{script_dir}/fbos.csv')[imp_var]
    df2 = pd.read_csv(f'{script_dir}/fbos1.csv')[imp_var]
    df = pd.concat([df1, df2], ignore_index=True)
    fbochecks(df)


# Send output to JSON for companion discord bot
    # Output to JSON for bot
def send_message(content):
    file_path = script_dir / cfg.filename
    if os.path.exists(file_path):
        
        if os.stat(file_path).st_size == 0:
            logger.info("\nMessage JSON appears to be empty, creating new data structure")
            file_data = {"notifications": [content]}
        else:
            with open(file_path, 'r') as file:
                file_data = json.load(file)
            file_data["notifications"].append(content)
    else:
        logger.warning("\nMessage JSON file not found, creating a new one")
        file_data = {"notifications": [content]}
    
    with open(file_path, 'w') as file:
        json.dump(file_data, file)

# Main checks Functions

def fbochecks(df):
# Check fo airport closure warning
    try:
        df.loc[df["SuppliedDays"] < cfg.supplies, "Warning"] = "True"
    except KeyError:
        print("error getting datafeed")
        logger.info("\nAn error occoured fetching datafeeds")
        send_message("\nAn error occoured fetching datafeeds")
        sys.exit(1)

    # Check for Fuel Resupply
    df.loc[df["FuelJetA"] < cfg.jet, "OrderJet"] = "True"
    df.loc[df["Fuel100LL"] < cfg.avgas, "OrderAvgas"] = "True"

    # Filter out airports with intentional zero fuel
    df.loc[df["PriceJetAGal"] == 0, "OrderJet"] = ""
    df.loc[df["Price100LLGal"] == 0, "OrderAvgas"] = ""

    # filter into warnings
    airport_warning = df.loc[df["Warning"] == "True"]
    airport_warning.shape
    jeta_resupply = df.loc[df["OrderJet"] == "True"]
    jeta_resupply.shape
    avgas_resupply = df.loc[df["OrderAvgas"] == "True"]
    avgas_resupply.shape

    # Airport Warnings Message
    if airport_warning.empty:
        message_str = "No Airport Supply Warnings"
    else:
        message_str = "Airports with supply warnings:\n {}".format(
            airport_warning[["Airport", "SuppliedDays"]].to_string(index=False)
        )
    logger.info("\n{}".format(message_str))
    send_message(message_str)

    # Jet A Orders
    if jeta_resupply.empty:
        message_str = "No JetA Orders Requried"
    else:
        message_str = "Airports requiring JetA Orders:\n {}".format(
            jeta_resupply[["Airport", "FuelJetA"]].to_string(index=False)
        )
    logger.info("\n{}".format(message_str))
    send_message(message_str)

    # Avgas Orders
    if avgas_resupply.empty:
        message_str = "No Avgas Orders Required"
    else:
        message_str = "Airports requiring Avgas Orders:\n {}".format(
            avgas_resupply[["Airport", "Fuel100LL"]].to_string(index=False)
        )
    logger.info("\n{}".format(message_str))
    send_message(message_str)


if __name__ == "__main__":
    createdataframe()