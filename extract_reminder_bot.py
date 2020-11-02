#http://discordpy.readthedocs.io/en/latest/api.html

import discord
from discord.ext import commands
from extract_reminder import reminderParse
import asyncio
import datetime
import parsedatetime

digits = {
    1: '\U00000031\U000020E3',
    2: "\U00000032\U000020E3",
    3: "\U00000033\U000020E3",
    4: "\U00000034\U000020E3",
    5: "\U00000035\U000020E3",
    6: "\U00000036\U000020E3",
    7: "\U00000037\U000020E3",
    8: "\U00000038\U000020E3",
    9: "\U00000039\U000020E3"
}
digits2 = {v: k for k, v in digits.items()}
remindersList = []
runningReminder = ()
currentReminder = 0
reminderChannel = 0
def command_prefix(bot, message):
    if message.guild is None:
        return ''
    else:
        return ';'
bot = commands.Bot(command_prefix=';')
bot.remove_command('help')
@bot.event
async def on_ready():
    global reminderChannel
    global remindersList
    global runningReminder
    global currentReminder
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for channel in bot.get_all_channels():
        # print(channel.name)
        if channel.name == "save-reminders":
            reminderChannel = channel
            break
    savedReminders = await reminderChannel.history().flatten()
    if len(savedReminders) > 0:
        savedReminders = [(str(msg.content), msg) for msg in savedReminders]
        reminderStrList = []
        for reminder in savedReminders:
            reminderStrList.append((reminder[0].split('\n'), reminder[1]))
        
        for reminder in reminderStrList:
            print(reminder[0][2])
            parsed_time = datetime.datetime.strptime(reminder[0][0], '%Y-%m-%d %H:%M:%S')
            if parsed_time > datetime.datetime.now():
                remindersList.append([parsed_time, reminder[0][1], bot.get_user(int(reminder[0][2])), reminder[1]])
            else:
                await reminder[1].delete()
        
        if len(remindersList) > 0:
            remindersList = sorted(remindersList, key=lambda x: x[0])
            time_left = (remindersList[0][0] - datetime.datetime.now()).total_seconds()
            if time_left < 86000:
                currentReminder = asyncio.create_task(remind_after(time_left, remindersList[0][1], remindersList[0][2]))
                runningReminder = remindersList[0]
            print(remindersList)
    

@bot.event
async def on_message(message):
    await bot.process_commands(message)

'''@bot.event
async def on_command_error(ctx, error):
    if(isinstance(error, commands.CommandNotFound)):
        await ctx.send(error.message.channel, "Command \"{0}\" is not found.".format(error.invoked_with))'''
async def remind_after(delay, what, user):
    global currentReminder
    global runningReminder
    global remindersList
    await asyncio.sleep(delay)
    await user.send("REMINDER: " + what)
    await remindersList[0][3].delete()
    try:
        snooze = await bot.wait_for('message', check=lambda message: message.author == user and message.guild == None, timeout=30)
    except asyncio.TimeoutError: 
        remindersList.pop(0)
        print(remindersList)
        if len(remindersList) > 0:
            time_left = (remindersList[0][0] - datetime.datetime.now()).total_seconds()
            if time_left < 86000:
                runningReminder = remindersList[0]
                currentReminder = asyncio.create_task(remind_after(time_left, runningReminder[1], runningReminder[2]))
        else:
            runningReminder = ()
    else:
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(snooze.content)
        snoozeTime=datetime.datetime(*time_struct[:6])     #getting the time from the query
        if(parse_status == 1):
            now = datetime.datetime.now()
            snoozeTime = snoozeTime.replace(hour=now.hour)
            snoozeTime = snoozeTime.replace(minute=now.minute)
            snoozeTime = snoozeTime.replace(second=now.second)
        remindersList[0][3] = await reminderChannel.send(str(snoozeTime) + '\n' + remindersList[0][1] + '\n' + str(remindersList[0][2].id))
        remindersList[0][0] = snoozeTime
        remindersList = sorted(remindersList, key=lambda x: x[0])
        time_left = (remindersList[0][0] - datetime.datetime.now()).total_seconds()
        if time_left < 86000:
            runningReminder = remindersList[0]
            currentReminder = asyncio.create_task(remind_after(time_left, runningReminder[1], runningReminder[2]))
        print(remindersList)
        await user.send("Snoozing until **" + str(snoozeTime.hour) + ':' + str(snoozeTime.minute) + ':' + str(snoozeTime.second) + ' on ' + str(snoozeTime.day) + '-' + str(snoozeTime.month) + '-' + str(snoozeTime.year) + "**")


async def check_reminders():
    global runningReminder
    global currentReminder
    if runningReminder == ():
        if remindersList[0] != None:
            time_diff = (remindersList[0][0] - datetime.datetime.now()).total_seconds()
            if time_diff < 86000:
                runningReminder = remindersList[0]
                currentReminder = asyncio.create_task(remind_after(time_diff, runningReminder[1], runningReminder[2]))
    await asyncio.sleep(3600)

@bot.command()
async def help(ctx):
    em = discord.Embed(description="How to use the NLP Reminder Bot", title="Reminder Bot Help", color=0X008CFF)
    em.add_field(name="Command", value="Start the command with ;rm me")
    em.add_field(name="Subject and time", value="Use natural language in your command. For example, ';rm me to do my math homework at 9:30am tomorrow'. The bot will recognize keywords like 'to', 'of', 'at', 'etc.'")
    em.add_field(name="Choosing the best reminder", value="Sometimes the bot will parse more than one possible reminder. If this happens, it will prompt you to react with the most accurate one.")
    em.add_field(name="Possible problems", value="The bot will assume AM instead of PM, so make sure to specify")
    await ctx.send(embed=em)
@bot.command()
async def rm(ctx, *, reminderString=None):
    global remindersList
    global runningReminder
    global currentReminder
    global reminderChannel

    print('reminding')
    rParsed = reminderParse(reminderString)
    print(rParsed)
    print('extracted')
    em = discord.Embed(description="Which of the following is most accurate?", title="New Reminder", color=0X008CFF)
    printedstr = "Which of the following is most accurate?\n"
    for k, reminder in enumerate(rParsed):
        print(reminder)
        time_set = reminder[1]
        print(time_set)
        day,month,year=time_set.day,time_set.month,time_set.year
        hour,mins,secs=time_set.hour,time_set.minute,time_set.second
        print('SUBJECT: ' + reminder[0] + ' TIME: ' + str(hour) + ':' + str(mins) + ':' + str(secs) + ' on ' + str(day) + '-' + str(month) + '-' + str(year))
        printedstr += '     ' + str(k + 1) + '. SUBJECT: ' + reminder[0] + ' TIME: ' + str(hour) + ':' + str(mins) + ':' + str(secs) + ' on ' + str(day) + '-' + str(month) + '-' + str(year) + '\n'
        embedStr = '     ' + ' **SUBJECT:** ' + reminder[0] + ' \n**TIME:** ' + str(hour) + ':' + str(mins) + ':' + str(secs) + ' on ' + str(day) + '-' + str(month) + '-' + str(year) + '\n'
        em.add_field(name=str(k + 1) + '.', value=embedStr)

    #await ctx.send(printedstr)
    def check(reaction, user):
        return user == message.author and str(reaction) in digits.values()

    choice = 0
    if(len(rParsed) > 1):
        remindermsg = await ctx.send(embed=em)
        for i in range(len(rParsed)):
            reaction = digits[i+1]
            await remindermsg.add_reaction(reaction)

        message = ctx.message
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        choice = digits2[str(reaction)] - 1
        print(choice, user)

    reminder_time = rParsed[choice][1]
    reminder_msg = rParsed[choice][0]
    day,month,year=reminder_time.day,reminder_time.month,reminder_time.year
    hour,mins,secs=reminder_time.hour,reminder_time.minute,reminder_time.second
    time_left = (reminder_time - datetime.datetime.now()).total_seconds()
    remindersList.append([reminder_time, reminder_msg, ctx.message.author, await reminderChannel.send(str(reminder_time) + '\n' + reminder_msg + '\n' + str(ctx.message.author.id))])
    remindersList = sorted(remindersList, key=lambda x: x[0])
    if runningReminder != ():
        same = True
        for i in range(3):
            if remindersList[0][i] != runningReminder[i]:
                same = False
        if not same:
            runningReminder = remindersList[0]
            reminder_time = runningReminder[0]
            reminder_msg = runningReminder[1]
            time_left = (reminder_time - datetime.datetime.now()).total_seconds()
            currentReminder.cancel()
            currentReminder = asyncio.create_task(remind_after(time_left, reminder_msg, ctx.message.author))           
            print(reminder_msg, time_left) 
    else:
        if time_left < 86000:
            currentReminder = asyncio.create_task(remind_after(time_left, reminder_msg, ctx.message.author))
            print(reminder_msg, time_left)
            runningReminder = remindersList[0]
    print(remindersList)
    await ctx.send("Reminding you to **" + reminder_msg + "** at **" + str(hour) + ':' + str(mins) + ':' + str(secs) + ' on ' + str(day) + '-' + str(month) + '-' + str(year) + "**")

@bot.command()
async def myrm(ctx):
    user = ctx.message.author
    usersReminders = []
    for reminder in remindersList:
        if remindersList[2] == user:
            usersReminders.append(reminder)

@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    await ctx.bot.logout()

bot.run('NzQ3NDg1Mjk5MDcyMDQwOTgw.X0Pj7g.IBaJ_cWP01MHxwf70LW8AqJ4WT0')