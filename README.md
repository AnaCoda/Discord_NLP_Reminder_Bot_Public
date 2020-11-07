# Discord_NLP_Reminder_Bot_Public
A Discord reminder bot that parses information from a natural reminder request and sends a message to remind you.

extract_reminder.py contains a function I use for the actual parsing of the input, and all the code I used to regex the templates from.

This project uses Python and extracts the subject and time from a Discord message like "remind me to do math homework at 6pm on tuesday" and reminds you to "do math homework" at 18:00 on Tuesday. It does so using templates and a library to parse the time. Asyncio is used for the reminders and discord.py for the Discord integration. 

Work in progress, as I am still figuring out how to properly use Asyncio and there are some bugs. 
