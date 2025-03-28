from canvasapi import Canvas
import discord, datetime, time, os
from discord import ButtonStyle
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
from keep_alive import keep_alive
from dotenv import load_dotenv, dotenv_values, set_key

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
    ushold = canvas.get_user(unhold[0: len(unhold) - len(str(totalUsers))], 'sis_login_id')
    course = ushold.get_courses(enrollment_state='active')
    #Then loops through each course
    for c in course:
        #And then loops through each courses assignments
        for o in c.get_assignments():
            if (o.due_at != None):
                #Calculates the time in hours before the assignment's due date, and the time in days as well for formatting
                timern = datetime.datetime.now()
                truetime = datetime.datetime.strptime(o.due_at, '%Y-%m-%dT%H:%M:%SZ')
                sendtime = str(truetime.strftime('%A')) + ", " + str(truetime.strftime('%b')) + " " + str(truetime.strftime('%d'))
                calc = truetime - timern
                hours = calc.total_seconds() // 3600
                days = int(hours // 24)
                #Then, if the hours before the due date is greater than 0 (meaning it doesnt count past due assignments) and lower than the target number of hours (48 as default)
                if (hours > 0 and hours < 48):
                    #Then, it creates a variable that checks the state of the current student's submission of this assignment, and if it's unsbmitted, add the assignment and its due date to the dm
                    sub = o.get_submission(ushold.id).workflow_state
                    if (sub == "unsubmitted"):
                        send += str(o)[0: str(o).find("(")] + ": Due in " + str(days) + " days on " + sendtime + " at " + str(truetime.strftime('%I'))[1:] + " " + str(truetime.strftime('%p')) + "\n"
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
@tasks.loop(hours = 12)
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
    if (message.content.startswith('$Remindme')):
        #Bot grabs the discord id of the user who sent the message
        user = await client.fetch_user(message.author.id)
        #Then checks to see if the user is in the list of registered users. If they aren't, stop them from running the command
        if (str(dotenv_values(".env")).find(str(user)) == -1):
            await message.channel.send("You are not signed up for the bot!")
        #If they are, creates a dm with them
        else:
            #Also creates a variable 'locate' that is used to get the index of the person accessing the bot currently through use of the env
            #It gets the substring of the entire env's contents that starts where the current user's discord username is, and ending where that value in the env ends
            locate = str(dotenv_values(".env"))[str(dotenv_values(".env")).find(str(user)): str(dotenv_values(".env")).find(str(user)) + len(str(user)) + len(str(totalUsers))]
            #Then, it makes another substring of itself that only includes the last few digits that are included in the value, which is the current user's index
            #It goes through all of this in order to access that user's rowan login and api key that they provided during their signup in order to access their courses
            locate = locate[len(locate) - len(str(totalUsers)):]
            canvas = Canvas("https://canvas.rowan.edu", str(dotenv_values(".env")['KEY_' + locate]))
            await client.create_dm(user)
            await user.send("You will be notified of any canvas assignments that are due the next day!")
            set_key(".env", "REMIND_" + locate, str("1"))
            

    #Code for tutorial command
    if (message.content.startswith('$Tutorial')):
        global test
        global viewer
        apiWorks = False
        loginWorks = False
        #Deletes the $Tutorial message from the user, and creates a new Tutorial button object
        user = await client.fetch_user(message.author.id)
        dm = await client.create_dm(user)
        await message.delete()
        #Checks to see if the username that's currently registering is already in the system via the env file, if they are, stops them from registering again
        if (str(dotenv_values(".env")).find(str(user)) != -1):
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
            time.sleep(0.75)
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
                        #Also adds the digits of the user's index onto the end of the USER value, as a way of accessing the index for other commands
                        set_key(".env", "USER_" + str(totalUsers), str(login.content) + str(totalUsers))
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
 
