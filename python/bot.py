import discord
from discord.ext import commands
import asyncio
import os
import json

dirname = os.path.dirname(__file__)
try:
    f = open(os.path.join(dirname, '../config/messages.json'))
    werewolfMessages = json.loads(f.read())
    f.close()
    f2 = open(os.path.join(dirname, "../config/command_descriptions.json"))
    commandDescriptions = json.loads(f2.read())
    f2.close()
    f3 = open(os.path.join(dirname, "../config/discord-config.json"))
    config = json.loads(f3.read())
    f3.close()
except FileNotFoundError:
    print("File not found")

bot = commands.Bot(command_prefix = '!')

@bot.event
async def on_ready():
    print("The werewolves are howling!")

@bot.command(pass_context = True)
async def exit(ctx):
    if ctx.message.channel.id == config["channels"]["bot-admin"]:
        await bot.say("Goodbye!")
        await bot.logout()
    else:
        await bot.say("I'm sorry, but you cannot shut me down!")
     
bot.run(config["token"])
