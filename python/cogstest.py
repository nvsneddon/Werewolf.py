import discord
import threading
import schedule
import time
from discord.ext import commands

class Test(commands.Cog):


    def timer(self):
        while not self.schedstop.is_set():
            schedule.run_pending()
            time.sleep(3)



    def __init__(self, client, age):
        self.client = client
        self.__age = age

        self.schedstop = threading.Event()
        self.schedthread = threading.Thread(target=self.timer)
        self.schedthread.start()

        schedule.every(5).minutes.do(self.nightschedule).tag("game")

    def nightschedule(self):
        print("Testing")
        self.client.loop.create_task(self.daytime())
        #await self.client.send(bot.get_channel(special_channels["bot-admin"]), "It is Nighttime!")

    def cog_unload(self):
        schedule.clear("game")
        return super().cog_unload()

    @commands.command(brief="I'm running this test!", description="This is a better description that will go more into details on how to work this.")
    async def testing(self, ctx):
        await ctx.send("I think this worked! The age is {}".format(self.__age))
        await self.daytime()
    
    async def daytime(self):
        await self.client.get_channel(532360369683955764).send("Does this really work?")