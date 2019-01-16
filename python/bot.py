import discord
from discord.ext import commands
import game
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

@bot.command()
async def echo(*args):
    output = ''
    for x in args:
        output += x
        output += ' '
    await bot.say(output)

@bot.command(pass_context = True)
async def clear(ctx, number=10):
    if (discord.utils.get(ctx.message.author.roles, name="Owner") is None) and (ctx.message.author != findPerson(ctx, "keyclimber")):
        await bot.say("You don't have permission to do this!")
        return
    number = int(number+1) #Converting the amount of messages to delete to an integer
    counter = 0
    async for x in bot.logs_from(ctx.message.channel, limit = number):
        if counter < number:
            if x.pinned:
                continue
            await bot.delete_message(x)
            counter += 1

@bot.command(pass_context = True)
async def exit(ctx):
    if ctx.message.channel.id == config["channels"]["bot-admin"]:
        await bot.say("Goodbye!")
        await bot.logout()
    else:
        await bot.say("I'm sorry, but you cannot shut me down!")
        
def findPerson(ctx, *args):
    if len(args) == 1:
        if type(args[0]) is str:   
            name = args[0]
        else:
            name = " ".join(args[0])
    else:
        print("Something went very wrong. Args is not of length 1")
        return None
     
bot.run(config["token"])
