import discord
from discord.ext import commands
from files import config
from bot import Bot

bot = commands.Bot(command_prefix='!')

@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        await ctx.send("Hey! No sending me commands here!")
    return ctx.guild is not None


@bot.event
async def on_ready():
    bot.add_cog(Bot(bot))
    print("The werewolves are howling!")


if __name__ == "__main__":
    bot.run(config["token"])
