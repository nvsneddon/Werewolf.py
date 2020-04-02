import discord
from discord.ext import commands

import files
import bot

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = commands.Bot(command_prefix='!')


@client.event
async def on_ready():
    client.add_cog(bot.Bot(client))
    print("The werewolves are howling!")


@client.event
async def on_guild_join(guild):
    files.writeJsonToConfig("server_config.json", {"server_id": str(guild.id)})
    if not discord.utils.get(guild.channels, name="bot-admin"):
        permissions = files.readJsonFromConfig('permissions.json')
        overwrite = {
            guild.default_role: discord.PermissionOverwrite(**permissions['none'])
        }
        await guild.create_text_channel(name="bot-admin")
        channel = discord.utils.get(guild.channels, name="bot-admin")
        await channel.send(
            "Hi there! I've made this channel for you. On here, you can be the admin to the bot. I'll let you decide "
            "who will be allowed to access this channel.\nHave fun :) "
        )
        # TODO Test to see if this works before deploying to other servers


@client.event
async def on_message(message):
    # if message.guild is None and (message.author != bot.user):
    #     if message.content.startswith("!respond"):
    #         delimiter = '#'
    #         response = message.content.split(delimiter)
    #         user_id = response[1]
    #         response_message = delimiter.join(response[2:])
    #         await message.author.send("The message has been sent!")
    #         await bot.get_guild().get_member(int(user_id)).send(
    #             f"Response : {response_message}")
    #     else:
    #         question = message.content + "\n" + str(message.author.id)
    #         await message.author.send("Thanks for submitting. Your question will be answered shortly.")
    #         await bot.get_guild().owner.send(question)
    # else:
    await client.process_commands(message)


if __name__ == "__main__":
    client.run(files.config["token"])
