import discord
from discord.ext import commands
import asyncio
import contextlib

#IDs (ints, replace with appropriate values)
BOT_ID = 000000000000000000
WELCOME_CHANNEL_ID = 000000000000000000 # where the welcome message is posted if a user is accepted
DEFAULT_CHANNEL_ID = 000000000000000000 # where default users can chat before getting accepted
PENDING_INTERVIEWS_CHANNEL_ID = 000000000000000000 # completed interviews will be posted here to be processed by staff
VERIFY_CHANNEL_ID = 000000000000000000 # where users may use the verify command to begin the interview process
ACCEPTED_INTERVIEWS_CHANNEL_ID = 000000000000000000 # all accepted interviews will be posted
DECLINED_INTERVIEWS_CHANNEL_ID = 000000000000000000 # all declined/jailed interviews will be posted here
ACCEPTED_ROLE_ID = 000000000000000000 # accepted member role or equivalent
DECLINE_ROLE_ID = 000000000000000000 # declined role or equivalent
JAIL_ROLE_ID = 000000000000000000 # jailed role or equivalent 
DEFAULT_ROLE_ID = 000000000000000000 # role the user is given when they join the server

QUESTIONS = ["1.) How old are you?",
            "2.) What gender do you identify as?", 
            "3.) Where did you find RetroGirly? If you were invited by a friend, what is their username and number? (Ex. Rebecca#2394)", 
            "4.) What about our server advertisement was enticing? (Ex. The Icon, The Name, Part of the Description)", 
            "5.) Why do you feel like a server made for women is a good fit for you?", 
            "6.) Women are treated unfairly online because of their gender everyday. Have you ever witnessed or received this treatment yourself? If you have, we'd love to hear a brief explanation of your experience.", 
            "7.) What is one fun fact about you?"]

HEADERS = ["Age", "Gender", "Referral", "AD Enticement", "Reason(s) for FOS", "Discrimination", "Fun Fact"]

class Interview(commands.Cog):

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == VERIFY_CHANNEL_ID:
            with contextlib.suppress(discord.NotFound):
                await message.delete()

    @commands.has_any_role(DEFAULT_ROLE_ID) #fix console from giving error message
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command()
    async def verify(self, ctx):
    # Allows a user to start the verification process through dms and posts their responses to the interviews channel
        if ctx.message.channel.id == VERIFY_CHANNEL_ID:
            answers = []
            author = ctx.author
            username = author.name + "#" + author.discriminator #eg. Marius#1337
            channel = await author.create_dm()
            try:
                await channel.send("**The verification process has begun!** *(7 Questions)*\n*Answers relating to your identity will not contribute to your eligibility to join.*")
            except: # if user has closed DMs
                await self.bot.get_channel(DEFAULT_CHANNEL_ID).send(f"{author.mention}, you must have open direct messages in order to get verified!\n\n> __**Instructions**__\n> *Settings* --> *Privacy & Safety* --> *Allow direct messages from server members*")
            else:
                for q in QUESTIONS:
                    await channel.send(q)
                    try:
                        msg = await self.bot.wait_for('message', check=lambda m: m.channel == channel and m.author == author and len(m.attachments) == 0, timeout=600) #checking if the message is sent by user in dms and text only.
                    except asyncio.TimeoutError:
                        await channel.send("**You took too long to respond.**\nPlease use the ~verify command again to restart the interview process.")
                        return
                    answers.append(msg.content)
                await channel.send("**Thank you for your patience!**\n*You will be notified when your application goes through.*")
                embed = discord.Embed(title=username, color=0xFFB6C1)
                embed.add_field(name="**ID**", value=author.id)
                for i in range(len(HEADERS)):
                    embed.add_field(name="**" + HEADERS[i] + "**", value=answers[i])
                interview_box = await self.bot.get_channel(PENDING_INTERVIEWS_CHANNEL_ID).send(embed=embed) #message which gets posted to reviews channel
                await interview_box.add_reaction("\U00002705") # reacts with green checkmark
                await interview_box.add_reaction("\U0000274C") # reacts with red cross
                await interview_box.add_reaction("\U000026D3") # reacts with chain emoji

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
    # Handles the accepting/declining of interviewees.
        user = payload.member
        if user.id != BOT_ID and payload.channel_id == PENDING_INTERVIEWS_CHANNEL_ID and (payload.emoji.name == "\U00002705" or payload.emoji.name == "\U0000274C" or payload.emoji.name == "\U000026D3"):
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            await msg.clear_reactions()
            interviewee = user.guild.get_member(int(msg.embeds[0].fields[0].value)) # gets user ID from embed and gets the member with that ID
            if interviewee != None: # if the user didn't leave after their interview was complete but not accepted or declined ...
                channel = await interviewee.create_dm()
                await interviewee.remove_roles(user.guild.get_role(DEFAULT_ROLE_ID))
                if payload.emoji.name == "\U00002705": # if accepted...
                    await interviewee.add_roles(user.guild.get_role(ACCEPTED_ROLE_ID))
                    await self.bot.get_channel(ACCEPTED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Accepted by {user.name + '#' + user.discriminator}"))
                    await channel.send("**Congratulations! Your application has been accepted.**\n*Please grab some self roles at our Front Desk.*")
                    await self.bot.get_channel(WELCOME_CHANNEL_ID).send(f"Welcome {interviewee.mention}!")
                elif payload.emoji.name == "\U0000274C": # if declined...
                    await interviewee.add_roles(user.guild.get_role(DECLINE_ROLE_ID))
                    await self.bot.get_channel(DECLINED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Declined by {user.name + '#' + user.discriminator}"))
                    await channel.send("**Your application has been denied by staff.**\n*Your application did not pass and your access to the entire server has been declined.*")
                elif payload.emoji.name == "\U000026D3": # if jailed...
                    await interviewee.add_roles(user.guild.get_role(JAIL_ROLE_ID))
                    await self.bot.get_channel(DECLINED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Jailed by {user.name + '#' + user.discriminator}"))
                    await channel.send("**Your application has been denied by staff and you have been jailed.**\n*Your application did not pass and your access to the entire server has been declined.*")

            else: # if the user left before being accepted/declined
                if payload.emoji.name == "\U00002705": # if accepted...
                    await self.bot.get_channel(ACCEPTED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Accepted by {user.name + '#' + user.discriminator}\nUser left before they were accepted."))
                elif payload.emoji.name == "\U0000274C": # if declined...
                    await self.bot.get_channel(DECLINED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Declined by {user.name + '#' + user.discriminator}\nUser left before they were declined."))
                elif payload.emoji.name == "\U000026D3":
                    await self.bot.get_channel(DECLINED_INTERVIEWS_CHANNEL_ID).send(embed=msg.embeds[0].set_footer(text=f"Jailed by {user.name + '#' + user.discriminator}\nUser left before they were declined."))
            await msg.delete()


def setup(bot):
    bot.add_cog(Interview(bot))