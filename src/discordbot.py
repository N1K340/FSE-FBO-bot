#!/usr/bin/env python3.9

"""
Python script to monitor for notifications JSON file output by FSE FBO operations
- Check every minute if JSON has a new notification
- Post to specified discord chanel 
- Output logs to '../logs/discordbot.log

Configuration required in file 'fsefbo.config'

"""


import discord
import fsefboconfigreal as cfg
import json
import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime

# setup the logger
logger = logging.getLogger(__name__)
if not os.path.exists(f"{os.path.dirname(__file__)}/logs/"):
    os.makedirs(f"{os.path.dirname(__file__)}/logs/")
logging.basicConfig(
    filename=f"{os.path.dirname(__file__)}/logs/discordbot.log",
    format="%(asctime)s:%(message)s",
    level=logging.INFO
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def send_notification(
    notification,
):  # this method is tested and works when called from same file
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == cfg.disco_channel:
                print(
                    "{} Message sent on discord - {}".format(
                        datetime.now(), notification
                    )
                )
                logger.info(f"\nNew notification found:\n{notification}")
                await channel.send(notification)


async def update_notifications():
    while True:
        try:
            script_dir = Path(__file__).resolve().parent
            file_path = script_dir / cfg.filename
            logger.info(f"\nChecking '{file_path}' for new messages.")

            with open(file_path, "r") as file:  # extract all content from json file
                content = json.load(file)
            while len(content["notifications"]) > 0:  # send all notifications one by one
                await send_notification(content["notifications"][0])
                content["notifications"].pop(0)
            with open(
                "disco_msg.json", "w"
            ) as file:  # write the now empty content back to json file
                json.dump(content, file, indent=4)
            await asyncio.sleep(60)
        except FileNotFoundError:
            print(f"The file '{cfg.filename}' was not found in the same directory as the script.")
            logger.warning(f"\nThe file '{cfg.filename}' was not found in the same directory as the script.")
            await asyncio.sleep(60)
            pass

if __name__ == "__main__":

    @client.event
    async def on_ready():
        client.loop.create_task(update_notifications())

    client.run(cfg.token)
