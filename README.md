# FSE-FBO-bot
Python script to check supplies and fuel requirements for FBO holdings, and tally monthly hourly rate costs for aircraft

**Script functions:**

main.py:
- Check FBO has more than X days of supplies on hand
- Check FBO which sells JetA has minimum amount on hand (Fuel price > $1)
- Check FBO which sells Avgas has minimum amount on hand (Fuel price > $1)
- Check how many hours aircraft flew previous month and calculate the amortised maintenance costs
- Output results to Discord via Webhook

**Useage**

Intended to be run as a docker container.
Environmental variables needed to be set for the following API keys
'FBOHOOK' : The Discord webhook for the FBO check messages to be sent to
'MXHOOK' : The Discord webhook for the monthly maintenance costs to be sent
'FSEUSER' : The FSE API key for the user
'FSEGROUP1' : The FSE API key for the first group of FBO holdings
'FSEGROUP2' : The FSE API key for the second group of FBO holdings


*webhook*<br>
Create a webhook url on the discord server, selecting the text channel to recieve messages in.
https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

With the generated webhook, paste it into the config file with surrounding "".

*FSE API keys*<br>
This section has three entries required from the FSE website.<br>
https://server.fseconomy.net/datafeeds.jsp

This program is not designed for personal FBO holdings, the minimum required is a personal datakey and a group datakey. If second group is not required, leave fsegroup2 blank, i.e. fsegroup2 = ""

*config.py Variables*<br>
These are the trigger points for the script to decide to notify you of an airport requiring something to be ordered.

supplies_threshold - The minimum number of days where you will start getting warnings that more supplies need to be ordered.

jet_threshold - The minimum quantity of JetA1 in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

avgas_threshold - The minimum quantity of Avgas in kilograms that will trigger a warning, providing the FBO sells the fuel for more than $1. If fuel price is set less than $1 the program will assume you wish to not maintain a sellable level on hand and ignore this warning.

aircraft - The dictionary of aircraft registrations that need calculating ie {'A36-002':700, 'A36-003':1000}

**Changelog**
v2.0
- Merged FBO and Monthly Maintenance cost scripts together
- restructured to run as a docker container

v1.1
- Changed message disemination to use discord webhooks instead of pushing messages to a secondary bot script

v1.0
- Initial release