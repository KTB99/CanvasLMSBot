from canvasapi import Canvas
import discord, datetime, time, os
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import Button, View, Select
from keep_alive import keep_alive
from dotenv import load_dotenv, dotenv_values, set_key

intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents = intents)

API_URL = "https://canvas.rowan.edu"

load_dotenv()

#course = user.get_courses(enrollment_state='active')
dates = []
trueDates = []
courses = []
pivots = []
assign = []
testlist = []
newline = 0

#Sets the variable for the total number of users to the value stored in the env file, as a way of indexing the users that register
if (str(dotenv_values(".env")).find("TOTAL_USERS") != -1):
    totalUsers = int(dotenv_values()['TOTAL_USERS'])
else:
    totalUsers = 0

#Saving the commented code below for later implementation 

#for i in range(4):
    #testlist.append(discord.SelectOption(label=str(i), value="test Option " + str(i), description=None, default=False))

#Loop for adding the assignments from each course into an array,
#Alongside their due dates.
#Also using "newline" to determine when to split into the next course
#for c in course:
    #pivots.append(newline)
    #courses.append(c)
    #for o in c.get_assignments():
        #assign.append(o)
        #newline += 1
        #dates.append(o.due_at)

#Loop for converting the dates of each assignment into proper time format.
#for d in dates:
    #if (d != None):
        #truetime = datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ')
        #trueDates.append(truetime.strftime("%c"))

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
 
    
#Event for commands, where you can define multiple commands,
@client.event
#by defining an "on_message" method.
async def on_message(message):
    dm = ""
    cc = 0
    #If statement for a specifc command, this one being for the reminder
    if (message.content.startswith('$Remindme')):
        #Bot grabs the discord id of the user who sent the message, and creates
        #a dm with them.
        user = await client.fetch_user(message.author.id)
        await client.create_dm(user)
        #Then, it loops through each assignement of a course, and adds the due
        #dates and assignment names into a message for each course
        for i in range(len(trueDates) + len(courses)):
            #And once it reaches the next course, send a dm which has all of the
            #previous course's assignments
            if i in pivots:
                if (i != 0):
                    await user.send(dm)
                    dm = ""
                dm += "For " + str(courses[cc]) + "\n"
                cc += 1
            elif (i < len(trueDates)):
                dm += str(assign[i]) + " - Due **" + str(trueDates[i]) + "**\n"

    #Code for tutorial command
    if (message.content.startswith('$Tutorial')):
        global test
        global viewer
        global totalUsers
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
                        set_key(".env", "USER_" + str(totalUsers), str(user))
                        set_key(".env", "TOTAL_USERS", str(totalUsers + 1))
                        totalUsers = int(dotenv_values()['TOTAL_USERS'])
                    except:
                        await user.send("That user login is incorrect, please try again!")

#The use of the keep_alive file is for the server hosting, where the method keeps the bot awake once its online      
keep_alive()
client.run(os.getenv("key"))
