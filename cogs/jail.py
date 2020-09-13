import discord
from discord.ext import commands

#ROLE IDS (ints only, change to appropriate values)
JAIL_ROLE_ID = 000000000000000000 # role given to send user to jail
STAFF_ID = 000000000000000000 # staff role to avoid staff from jailing eachother

class Jail(commands.Cog):
    # removes a user's roles and gives them the jail role

    def __init__(self,bot):
        self.bot = bot

    @commands.has_any_role(STAFF_ID)
    @commands.command(aliases=["arrest"])
    async def jail(self, ctx, *, member: discord.Member):
        if len(ctx.message.mentions) == 1:
            roles = member.roles
            if ctx.guild.get_role(STAFF_ID) not in roles:
                await member.remove_roles(*(roles[1:]))
                await ctx.channel.send(f"{member.name + '#' + member.discriminator} has been sent to jail.")
                await member.add_roles(member.guild.get_role(JAIL_ROLE_ID))
            else:
                await ctx.channel.send("**MUTINY DETECTED**\nYou cannot jail a fellow staff member.")


def setup(bot):
    bot.add_cog(Jail(bot))