import discord
from discord.ext import commands
from files import config, writeJsonToConfig, writeToConfig
from bot import Bot

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    bot.add_cog(Bot(bot))
    print("The werewolves are howling!")


@bot.event
async def on_guild_join(self, guild):
    writeJsonToConfig("server_config.json", {"server_id": str(guild.id)})
    if not discord.utils.get(guild.channels, name="bot-admin"):
        await guild.create_text_channel(name="bot-admin")
        channel = discord.utils.get(guild.channels, name="bot-admin")
        await channel.send(
            "Hi there! I've made this channel for you. On here, you can be the admin to the bot. I'll let you decide who will be allowed to access this channel.\nHave fun :)")
        # TODO make it so that only the owner gets permission to this channel


@bot.event
async def on_message(message):
    if message.guild is None and (message.author != bot.user):
        if message.content.startswith("!respond"):
            response = message.content.split("#")
            await message.author.send("The message has been sent!")
            await bot.get_server(523892810319921157).get_member(response[1]).send(response[2])
        else:
            question = message.content + "\n" + str(message.author.id)
            await message.author.send("Thanks for submitting. Your question will be answered shortly.")
            await bot.get_guild(523892810319921157).get_member(352141925635063818).send(question)
    else:
        await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(config["token"])
