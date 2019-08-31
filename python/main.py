import discord
from discord.ext import commands
from files import config
from bot import Bot

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    bot.add_cog(Bot(bot))
    print("The werewolves are howling!")


if __name__ == "__main__":
    bot.run(config["token"])
