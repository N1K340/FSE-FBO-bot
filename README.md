# FSE-FBO-bot
Simple python script to check supplies and fuel requirements for FBO holdings

**Script functions:**

fsefbo.py:
- Check FBO has more than X days of supplies on hand
- Check FBO which sells JetA has minimum amount on hand (Fuel price > $1)
- Check FBO which sells Avgas has minimum amount on hand (Fuel price > $1)
- Output results to Discord via Webhook

**Useage**

Using crontab or similar, schedule fsefbo.py to run once or twice per day.
FSE Datafeeds are limited to 10 polls in 60 seconds, and 40 polls in 6 hours. There is limited value in increasing the fsefbo.py script to run beyond a couple of times a day.

**Setup**

The following items are required to be set in the 'fsefboconfig' file using a text editor:

*fbowebhook*<br>
Create a webhook url on the discord server, selecting the text channel to recieve messages in.
https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

With the generated webhook, paste it into the config file with surrounding "".

*FSE Datafeed keys*<br>
This section has three entries required from the FSE website.<br>
https://server.fseconomy.net/datafeeds.jsp

fseuser is the personal datakey tied to your account.
fsegroup1 / fsegroup2 are the datakeys for the groups holding the FBO assets.
This program is not designed for personal FBO holdings, the minimum required is a personal datakey and a group datakey. If second group is not required, leave fsegroup2 blank, i.e. fsegroup2 = ""

*FBO Check Variables*<br>
These are the trigger points for the script to decide to notify you of an airport requiring something to be ordered.

supplies_threshold - The minimum number of days where you will start getting warnings that more supplies need to be ordered.

jet_threshold - The minimum quantity of JetA1 in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

avgas_threshold - The minimum quantity of Avgas in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

**Changelog**
v1.1
- Changed message disemination to use discord webhooks instead of pushing messages to a secondary bot script

v1.0
- Initial release