import discord
from discord.ext import commands
from files import config
from bot import Bot

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    bot.add_cog(Bot(bot))
    print("The werewolves are howling!")

@bot.event
async def on_message(message):
    if message.guild is None and (message.author != bot.user):
        if message.content.startswith("!respond"):
            response = message.content.split("#")
            await message.author.send("The message has been sent!")
            await bot.get_server(523892810319921157).get_member(response[1]).send(response[2])
        else:
            question = message.content + "\n" + str(message.author.id)
            await message.author.send("Thanks for submitting.")
            await bot.get_guild(523892810319921157).get_member(352141925635063818).send(question)
    else:
        await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(config["token"])
