from canvasapi import Canvas
from datetime import timedelta
import discord, datetime, time, os
from discord import ButtonStyle
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
from keep_alive import keep_alive
from dotenv import load_dotenv, dotenv_values, set_key
from datetime import timedelta

intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents = intents)

API_URL = "https://canvas.rowan.edu"

load_dotenv()

canvas = None
ce = True

#Sets the variable for the total number of users to the value stored in the env file, as a way of indexing the users that register
if (str(dotenv_values(".env")).find("TOTAL_USERS") != -1):
    totalUsers = int(dotenv_values()['TOTAL_USERS'])
else:
    totalUsers = 0

#Method used for checking the dates of each students courses
def check_dues(i):
    global newline
    send = ""
    #Connects to the current user that the loop is on, denoted by i, and accesses their canvas courses using the information they gave during registration
    canvas = Canvas("https://canvas.rowan.edu", str(dotenv_values()['KEY_' + str(i)]))
    unhold = str(dotenv_values()['USER_' + str(i)])
    ushold = canvas.get_user(unhold, 'sis_login_id')
    course = ushold.get_courses(enrollment_state='active')
    timern = datetime.datetime.now()
    #Then loops through each course
    for c in course:
        assigns = c.get_assignments(bucket="unsubmitted")
        #And then loops through each courses assignments
        for o in assigns:
            if (o.due_at != None and ((datetime.datetime.strptime(o.due_at, '%Y-%m-%dT%H:%M:%SZ') - timern).total_seconds() // 3600 > 0 and (datetime.datetime.strptime(o.due_at, '%Y-%m-%dT%H:%M:%SZ') - timern).total_seconds() // 3600 < 48)):
                #Calculates the time in hours before the assignment's due date, and the time in days as well for formatting
                truetime = datetime.datetime.strptime(o.due_at, '%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(hours=4)
                #Then, if the hours before the due date is greater than 0 (meaning it doesnt count past due assignments) and lower than the target number of hours (48 as default)
                #Then, it creates a variable that checks the state of the current student's submission of this assignment, and if it's unsbmitted, add the assignment and its due date to the dm
                sendtime = str(truetime.strftime('%A')) + ", " + str(truetime.strftime('%b')) + " " + str(truetime.strftime('%d'))
                days = int(((datetime.datetime.strptime(o.due_at, '%Y-%m-%dT%H:%M:%SZ') - timern).total_seconds() // 3600) // 24)
                send += str(o)[0: str(o).find("(")] + ": Due in " + str(days) + " days on " + sendtime + " at " + str(truetime.strftime('%I')) + " " + str(truetime.strftime('%p')) + "\n"
    return send

#Class for tutorialbutton
class TutorialButton(discord.ui.View):
    #Definition of the pages of the tutorial, which will change when the user presses one of the buttons at the bottom
    def __init__(self):
        self.page = 0
        self.pages = ["Here's a quick tutorial to help get you get connected with the bot!\nClick the 'Next' button to begin!",
        "**Step 1/4:**\nClick this link to open up your Canvas account settings.\nhttps://canvas.rowan.edu/profile/settings\n(Log in if necessary)",
        "**Step 2/4:**\nScroll down until you find the 'Approved Integrations' section.\nIn that section, find and click the 'New Access Token' button.",
        "**Step 3/4:**\nNow on the 'New Access Token' window, simply enter 'CanvasPython' into the purpose line,\nand click the 'Generate Token' button.",
        "**Step 4/4:**\nFinally, copy the token that generated in the 'Token' section, and send it here to connect the bot!"]
        self.embed= discord.Embed(
            title = "Bot Connection Tutorial",
            description = self.pages[self.page],
            color = discord.Color.blue()
            )
        super().__init__()

    #Displays the 'Previous' button for the message
    @discord.ui.button(style=discord.ButtonStyle.blurple,label="<- Previous", disabled=True)
    #If the player clicks on the button, move the pages back one, and edit the bot's message to reflect that
    async def prev(self, interaction = discord.Interaction, button1 = Button()):
        self.page -= 1 
        #If this happens and the bot is back on the first page, disable the buttton to prevent any errors
        if (self.page == 0):
            button1.disabled = True
        #Also, enable the 'Next' button as well, since if we're going back a page, we'll always be able to click 'Next'
        viewer.next.disabled = False
        self.embed.description = self.pages[self.page]
        await interaction.response.edit_message(embed = self.embed, view = viewer)
        
    #Displays the 'Next' button for the message
    @discord.ui.button(style=discord.ButtonStyle.blurple,label="Next ->", disabled=False)
    #Similar code as the code for the 'Previous' button, just moving the page forward one instead
    async def next(self, interaction = discord.Interaction, button = Button()):
        self.page += 1
        if (self.page == len(self.pages) - 1):
            button.disabled = True
        viewer.prev.disabled = False
        self.embed.description = self.pages[self.page]
        await interaction.response.edit_message(embed = self.embed, view = viewer)
        
    
#Event used to confirm that the bot has signed on
@client.event
async def on_ready():
    print(f'Signed on as {client.user}')
    remind_check.start()

#Method for checking each user that is registered for the bot
@tasks.loop(hours = 24)
async def remind_check():
    for i in range(totalUsers):
        #Goes through the number of users in the register list, and uses that number, i, to access the information of that current user (So the first person to register is under 'USER_0', the second is 'USER_1', and so on)
        #It checks to see if that specific user signed up to be reminded for their classes via the 'REMIND' variable stored in the env file
        torf = str(dotenv_values()['REMIND_' + str(i)]) == str(1)
        #If they are signed up (The variable torf checks to see if the value in the REMIND variable is 1 or not), then access the user's information through canvas using the values in the env, and send the user the list of their upcoming assignments in dms
        if (torf):
            name = str(dotenv_values()['LOGIN_' + str(i)])
            user = await client.fetch_user(name)
            await client.create_dm(user)
            holdsend = check_dues(i)
            if (holdsend != ""):
                await user.send(check_dues(i))
    
#Event for commands, where you can define multiple commands,
@client.event
#by defining an "on_message" method.
async def on_message(message):
    global totalUsers
    dm = ""
    cc = 0
    #If statement for a specifc command, this one being for the reminder
    if (message.content.startswith('$Remindme') or message.content.startswith('$remindme')):
        #Bot grabs the discord id of the user who sent the message
        user = await client.fetch_user(message.author.id)
        #Then checks to see if the user is in the list of registered users. If they aren't, stop them from running the command
        if (str(dotenv_values(".env")).find(str(message.author.id)) == -1):
            await message.channel.send("You are not signed up for the bot!")
        #If they are, creates a dm with them
        else:
            #Also creates a variable 'locate' that is used to get the index of the person accessing the bot currently through use of the env
            #It gets the substring of the entire env's contents that starts where the current user's discord username is -5 to get the index of the user
            locate = str(dotenv_values(".env"))[str(dotenv_values(".env")).find(str(message.author.id)) - 5: str(dotenv_values(".env")).find(str(message.author.id)) - 4]
            canvas = Canvas("https://canvas.rowan.edu", str(dotenv_values(".env")['KEY_' + locate]))
            await client.create_dm(user)
            await user.send("You will be notified of any canvas assignments that are due the next day!")
            set_key(".env", "REMIND_" + locate, str("1"))
            
    #Next for removing yourself from the reminder list
    if (message.content.startswith('$Removeme') or message.content.startswith('$removeme')):
        user = await client.fetch_user(message.author.id)
        if (str(dotenv_values(".env")).find(str(message.author.id)) == -1):
            await message.channel.send("You are not signed up for the bot!")

        else:
            locate = str(dotenv_values(".env"))[str(dotenv_values(".env")).find(str(message.author.id)) - 5: str(dotenv_values(".env")).find(str(message.author.id)) - 4]
            if (str(dotenv_values()["REMIND_" + locate]) == '0'):
                await message.channel.send("You are not signed up for reminders!")

            else:
                await client.create_dm(user)
                await user.send("You have been removed from the reminder list!")
                set_key(".env", "REMIND_" + locate, str("0"))
                

    #Next for a basic help command that'll dm the user the commands that the bot has
    if (message.content.startswith('$Help') or message.content.startswith('$help')):
        userH = await client.fetch_user(message.author.id)
        dmH = await client.create_dm(userH)
        await userH.send("**CANVAS BOT COMMANDS**"
                        + "\n\n**$Connect**: A tutorial for connecting your canvas account to the bot, allowing use of all other commands!"
                        + "\n\n**$Remindme**: This command with put you on the bot's list of students to DM anytime they have an assignment that is due in 48 hours or less, reminding every 24 hours!"
                        + "\n\n**$Removeme**: If you ever need to remove yourself from the bot's list of reminders, you can use this command to take yourself off of it!"
                        + "\n\n**$Calendar**: If you ever want a list of all of your upcoming assignments, you can use this command to get a list of all of them in your dms!"
                        + "\n\n**$Grades**:   This command allows you to view your grades and graded assignments in a given class!")


    #Next for displaying the student's calendar
    if(message.content.startswith('$Calendar') or message.content.startswith('$calendar')):
        #Variables for the message that the bot will send the user, alongside a count for the number of characters in the message (since discord has a max message size of 5k characters)
        calSend = ""
        calNum = 0
        #Alongside variables for the message user, a dm with that user, the time right now, the variable we use to find the index of the user that's messaging, the canvas object, the user object, and their courses
        userDMC = await client.fetch_user(message.author.id)
        dmC = await client.create_dm(userDMC)
        if(str(dotenv_values(".env")).find(str(message.author.id)) == -1):
            message.channel.send("You are not signed up for the bot!")
        else:
            locateC = str(dotenv_values(".env"))[str(dotenv_values(".env")).find(str(message.author.id)) - 5: str(dotenv_values(".env")).find(str(message.author.id)) - 4]
            canvas = Canvas("https://canvas.rowan.edu", str(dotenv_values()['KEY_' + str(locateC)]))
            userC = canvas.get_user(dotenv_values()['USER_' + str(locateC)], 'sis_login_id')
            courseC = userC.get_courses(enrollment_state='active')
            calSend += "**UPCOMING ASSIGNMENTS**\n"
            #For each course in the user's canvas, add the course's name onto the send message
            for cC in courseC:
                yes = False
                calSend += "**__For " + str(cC.name) + "__**\n"
                assignsC = cC.get_assignments(bucket="upcoming")
                #Then loop through each upcoming assignment in the course,
                for aC in assignsC:
                    holdtimeC = datetime.datetime.strptime(aC.due_at, '%Y-%m-%dT%H:%M:%SZ')  - datetime.timedelta(hours=4)
                    truetimeC = int((datetime.datetime.now() - holdtimeC).total_seconds() // 86400)
                    #and if the number of days is less than 31 (meaning it's a calendar of the student's month of upcoming assignments), then add the name of the assignment and the due date to the send message
                    if (truetimeC < 31):
                        yes = True
                        calSend += "**" + str(aC.name) + "** Due on " + str(holdtimeC.strftime("%A")) + ", " + str(holdtimeC.strftime("%B")) + " " + str(holdtimeC.strftime("%d")) + " at " + str(holdtimeC.strftime("%I")) + ":" + str(holdtimeC.strftime("%M")) + " " + str(holdtimeC.strftime("%p")) + "\n"
                        calNum = len(calSend)
                        #Also check to see if the number of characters in the message is above 4750, meaning it's approaching the 5000 character discord limit, then send the message to restart the character limit
                        if (calNum > 4750):
                            await userC.send(calSend)
                            calNum = 0
                            calSend = ""
                #USing the 'yes' bool, we can check to see if any assignments got found for each course, and if not, add a message about that to the send message
                if (yes == False):
                    calSend += "You have no upcoming assignments this month!\n\n"
                #Otherwise, just add a new line to prep for the next course
                else:
                    calSend += "\n"
            #Once everything's been looped through, send the message to the user
            await userDMC.send(calSend)


    #Next to display grades in a class of the user's choice
    if(message.content.startswith('$Grades') or message.content.startswith('$grades')):
        userDMG = await client.fetch_user(message.author.id)
        dmG = await client.create_dm(userDMG)
        if(str(dotenv_values(".env")).find(str(message.author.id)) == -1):
            message.channel.send("You are not signed up for the bot!")
        else:
            message1 = ""
            #Display all courses available, and lets the user select the one they want to see their grades in.
            message1 += "**Which class would you like to view grades for?**\n**Please select the course ID.**\n"
            locateG = str(dotenv_values(".env"))[str(dotenv_values(".env")).find(str(message.author.id)) - 5: str(dotenv_values(".env")).find(str(message.author.id)) - 4]
            canvas = Canvas("https://canvas.rowan.edu", str(dotenv_values()['KEY_' + str(locateG)]))
            userG = canvas.get_user(dotenv_values()['USER_' + str(locateG)], 'sis_login_id')
            courseG = userG.get_courses(enrollment_state='active')
            for cG in courseG:
                message1 += str(cG.id) + ": " + str(cG.name) + "\n"
            await userDMG.send(message1)
            #Create a loop to allow the user to insert the name of a class
            validCourse = False
            while (validCourse == False):
                message2 = ""
                mess = await client.wait_for("message", check=lambda msg: msg.author == message.author, timeout = 300.0)
                myCourse = None
                for cG in courseG:
                    if (mess.content == str(cG.id)):
                        validCourse = True
                        myCourse = cG
                        break
                if validCourse:
                    earned = 0
                    total = 0
                    earned_ungraded = 0
                    total_ungraded = 0
                    assignsG = cG.get_assignments()
                    for aG in assignsG:
                        if aG.points_possible:
                            total_ungraded += aG.points_possible
                            submission = aG.get_submission(userG.id)  # Fetch the submission for the user
                            if submission and submission.score is not None:
                                earned += submission.score
                                total += aG.points_possible
                            else:
                                earned_ungraded += 0  # Ungraded assignments treated as 0
                    grade_with_ungraded = (earned / total_ungraded) * 100 if total_ungraded > 0 else 0
                    grade_without_ungraded = (earned / total) * 100 if total > 0 else 0
                    message2 = f"Current grade in {myCourse.name} is: {grade_without_ungraded:.2f}% (currently) or {grade_with_ungraded:.2f}% (including ungraded assignments)\n\n"
                    await userDMG.send(message2)
            
            


            
    #Next for the connection tutorial
    if (message.content.startswith('$Connect') or message.content.startswith('$connect')):
        global test
        global viewer
        apiWorks = False
        loginWorks = False
        #Deletes the $Tutorial message from the user, and creates a new Tutorial button object
        user = await client.fetch_user(message.author.id)
        dm = await client.create_dm(user)
        await message.delete()
        #Checks to see if the username that's currently registering is already in the system via the env file, if they are, stops them from registering again
        if (str(dotenv_values(".env")).find(str(user.id)) != -1):
            apiWorks = True
            loginWorks = True
            await message.channel.send("You have already signed up for the bot!")
        #Otherwise, sends the created Tutorial button to their dms
        else:
            viewer = TutorialButton()
            test = await user.send(embed = TutorialButton().embed, view = viewer)
            #Then waits for the original message user to send their API key in the chat 
            while (apiWorks == False):
                mess = await client.wait_for("message", check=lambda msg: msg.author == message.author, timeout = 300.0)
                #The bot also checks to make sure that the message was sent in their dms, as to not accidentally respond to messages in the server
                if (mess.channel.id == dm.id):
                    await user.send("Connecting to API key...")
                    #Once they send it over, the bot will try to verify the API key sent, and if it doesn't work, tell the user to try again
                    try:
                        hold = mess.content
                        canvas = Canvas("https://canvas.rowan.edu", hold)
                        canvas.get_current_user()
                        await user.send("Connected!")
                        apiWorks = True
                    except:
                        await user.send("That API code is incorrect, please try again!")
            #After the API key has been verified, then ask the user for their rowan username
            rest = await user.send(embed = discord.Embed(
                title = "User Login",
                description = "Nice job, the bot is now connected to your Canvas account, now all you have to do is login!\nSimply send your Rowan username (without the email part) to login!",
                color = discord.Color.blue()
                )
                )
            #Once they input their username, use another while loop to verify that it works, and connect to the student's account
            while (loginWorks == False):
                login = await client.wait_for("message", check=lambda msg: msg.author == message.author, timeout = 60.0)
                if (login.channel.id == dm.id):
                    try:
                        username = canvas.get_user(login.content, 'sis_login_id')
                        await user.send("Logged in! Welcome, " + str(username.name[0:username.name.find(' ')])+ "!")
                        loginWorks = True
                        #Once connected, the env file has the discord username of the person registering to the env file as a way of keeping them saved into the system
                        set_key(".env", "USER_" + str(totalUsers), str(login.content))
                        set_key(".env", "LOGIN_" + str(totalUsers), str(message.author.id))
                        set_key(".env", "KEY_" + str(totalUsers), str(hold))
                        set_key(".env", "REMIND_" + str(totalUsers), str("0"))
                        set_key(".env", "TOTAL_USERS", str(totalUsers + 1))
                        totalUsers = int(dotenv_values()['TOTAL_USERS'])
                    except:
                        await user.send("That user login is incorrect, please try again!")

#The use of the keep_alive file is for the server hosting, where the method keeps the bot awake once its online      
keep_alive()
client.run(os.getenv("key"))
 
