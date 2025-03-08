import os
from canvasapi import Canvas
import discord
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import Button, View, Select
import datetime
import time
from keep_alive import keep_alive
from dotenv import load_dotenv  # Import dotenv to load environment variables

# Load environment variables
load_dotenv()

# Secure API key retrieval
API_URL = "https://canvas.rowan.edu"
API_KEY = os.getenv("API_KEY")  # Canvas API key (loaded securely)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Discord bot token (loaded securely)

# Check if API keys are set properly
if not API_KEY or not DISCORD_TOKEN:
    raise ValueError("❌ Missing API Keys! Set them in .env or Replit Secrets Manager.")

# Discord bot setup
intents = discord.Intents.all()
intents.message_content = True
client = discord.Client(intents=intents)

# Keep the bot alive on Replit
keep_alive()

# Variables to store assignment data
dates = []
trueDates = []
courses = []
pivots = []
assign = []
testlist = []
newline = 0
globalpage = 0

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

#Class for tutorial button
class TutorialButton(discord.ui.View):
    #Definition of the pages of the tutorial, which will change when the user presses one of the buttons at the bottom
    def __init__(self):
        self.page = 0
        self.pages = [
            "Here's a quick tutorial to help get you connected with the bot!\nClick the 'Next' button to begin!",
            "**Step 1/4:**\nClick this link to open up your Canvas account settings.\nhttps://canvas.rowan.edu/profile/settings\n(Log in if necessary)",
            "**Step 2/4:**\nScroll down until you find the 'Approved Integrations' section.\nIn that section, find and click the 'New Access Token' button.",
            "**Step 3/4:**\nNow on the 'New Access Token' window, simply enter 'CanvasPython' into the purpose line,\nand click the 'Generate Token' button.",
            "**Step 4/4:**\nFinally, copy the token that generated in the 'Token' section, and send it here to connect the bot!"
        ]
        self.embed = discord.Embed(
            title="Bot Connection Tutorial",
            description=self.pages[globalpage],
            color=discord.Color.blue()
        )
        super().__init__()

    # Displays the 'Previous' button for the message
    @discord.ui.button(style=discord.ButtonStyle.blurple, label="<- Previous", disabled=True)
    async def prev(self, interaction: discord.Interaction, button1: Button):
        # If the player clicks on the button, move the pages back one, and edit the bot's message to reflect that
        self.page -= 1
        global globalpage
        globalpage -= 1
        if self.page == 0:
            button1.disabled = True  # Disable button if back on first page
        viewer.next.disabled = False  # Enable 'Next' button
        await interaction.response.edit_message(embed=TutorialButton().embed, view=viewer)

    # Displays the 'Next' button for the message
    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Next ->")
    async def next(self, interaction: discord.Interaction, button: Button):
        # Move the page forward one
        self.page += 1
        if self.page == len(self.pages) - 1:
            button.disabled = True  # Disable 'Next' on last page
        if self.page > 0:
            global globalpage
            globalpage += 1
        viewer.prev.disabled = False  # Enable 'Previous' button
        await interaction.response.edit_message(embed=TutorialButton().embed, view=viewer)

# Event used to confirm that the bot has signed on
@client.event
async def on_ready():
    print(f'✅ Signed on as {client.user}')

# Event for commands, where you can define multiple commands
@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Prevent bot from responding to its own messages

    dm = ""
    cc = 0

    # If statement for a specific command, this one being for the reminder
    if message.content.startswith('$Remindme'):
        # Bot grabs the Discord ID of the user who sent the message and creates a DM with them.
        user = await client.fetch_user(message.author.id)
        await client.create_dm(user)

        # Loops through each assignment of a course and adds the due dates and assignment names into a message
        for i in range(len(trueDates) + len(courses)):
            if i in pivots:  # If it's the next course, send a new message
                if i != 0:
                    await user.send(dm)
                    dm = ""
                dm += "For " + str(courses[cc]) + "\n"
                cc += 1
            elif i < len(trueDates):
                dm += str(assign[i]) + " - Due **" + str(trueDates[i]) + "**\n"

    # Code for tutorial command
    if message.content.startswith('$Tutorial'):
        global test, viewer
        apiWorks = False
        loginWorks = False

        # Deletes the $Tutorial message from the user, creates a new Tutorial button object, and sends it as a message
        user = await client.fetch_user(message.author.id)
        dm = await client.create_dm(user)
        await message.delete()
        viewer = TutorialButton()
        test = await user.send(embed=TutorialButton().embed, view=viewer)

        # Waits for the user to send their API key in DM
        while not apiWorks:
            mess = await client.wait_for("message", check=lambda msg: msg.author == message.author, timeout=300.0)
            if mess.channel.id == dm.id:
                await user.send("Connecting to API key...")
                try:
                    hold = mess.content
                    canvas = Canvas(API_URL, hold)
                    canvas.get_current_user()
                    await user.send("✅ Connected!")
                    apiWorks = True
                except:
                    await user.send("❌ That API code is incorrect, please try again!")

        time.sleep(0.75)

        # Ask the user for their Rowan username
        await user.send(embed=discord.Embed(
            title="User Login",
            description="Nice job! Send your Rowan username (without the email part) to log in.",
            color=discord.Color.blue()
        ))

        while not loginWorks:
            login = await client.wait_for("message", check=lambda msg: msg.author == message.author, timeout=60.0)
            try:
                username = canvas.get_user(login.content, 'sis_login_id')
                await user.send(f"✅ Logged in! Welcome, {username.name.split(' ')[0]}!")
                loginWorks = True
            except:
                await user.send("❌ That user login is incorrect, please try again!")


# Run bot securely
client.run(DISCORD_TOKEN)
