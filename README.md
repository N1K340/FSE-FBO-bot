# FSE-FBO-bot
Simple python script to check supplies and fuel requirements for FBO holdings

**Script functions:**

fsefbo.py:
- Check FBO has more than X days of supplies on hand
- Check FBO which sells JetA has minimum amount on hand (Fuel price > $1)
- Check FBO which sells Avgas has minimum amount on hand (Fuel price > $1)
- Output results to JSON for a discord bot to disseminate
- Output results to '../logs/fsefbo.log'

discordbot.py:
- Check every minute if JSON has a new notification
- Post to specified discord channel
- Resave JSON file minus disseminated messages
- Output logs to '../logs/discordbot.log

**Useage**

Using crontab or similar, set discorbot.py to run on reeboot and schedule fsefbo.py to run once or twice per day.
FSE Datafeeds are limited to 10 polls in 60 seconds, and 40 polls in 6 hours. There is limited value in increasing the fsefbo.py script to run beyond a couple of times a day.

**Setup**

The following items are required to be set in the 'fsefboconfig' file using a text editor:

*token*<br>
This is the discord app / bot token key.
Create an app and invite it to your server, copy the discord app token into the token field.<br>
i.e. token ="8746gg84fds8g48s4g6"

*disco_channel*<br>
This is the name of the chanel you have created on discord that the bot will post to.<br>
i.e. disco_channel = "fse-fbo-bot"

*FSE Datafeed keys*<br>
This section has three entries required from the FSE website.<br>
https://server.fseconomy.net/datafeeds.jsp

fseuser is the personal datakey tied to your account.
fsegroup1 / fsegroup2 are the datakeys for the groups holding the FBO assets.
This program is not designed for personal FBO holdings, the minimum required is a personal datakey and a group datakey. If second group is not required, leave fsegroup2 blank, i.e. fsegroup2 = ""

*FBO Check Variables*<br>
These are the trigger points for the script to decide to notify you of an airport requiring something to be ordered.

supplies - The minimum number of days where you will start getting warnings that more supplies need to be ordered.

jet - The minimum quantity of JetA1 in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

avgas - The minimum quantity of Avgas in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

*jsonfile*<br>
This is the name you wish the two scripts to use for the JSON file which communicates messages between each other. It is set default to fsedisco_msg.json, however may be altered for compatability reasons with other scripts if required.
