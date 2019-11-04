import discord
from discord.ext import commands
from villager import Villager

class Werewolf(commands.Cog, Villager):

    @commands.check
    def is_werewolf():
        async def predicate(ctx):
            return ctx.channel == discord.utils.get(ctx.guild.channels, name="werewolf")
        return commands.check(predicate)

    
    @commands.command
    @is_werewolf
    async def kill(self, ctx, *args):
        if len(args) > 1:
            ctx.send("You can only kill one person at a time.")
            return
        if len(args) == 0:
            ctx.send("Please say who you want to kill.")
            return
        target: str = args[0]
        return

        killedPlayer = self.findVillager(target)
        if killedPlayer.isProtected():
            await ctx.send("Nice try, but this person has been protected")
            # TODO Maybe consider announcing that the werewolves tried to kill someone that was protected
            killedPlayer.unprotect()
        elif killedPlayer != None:
            channel = bot.get_channel(special_channels["town-square"])
            await bot.say("You have killed {}".format(killed_user.display_name))
            await bot.send_message(channel, werewolfMessages[killedPlayer.character]["killed"].format(killed_user.mention))
            #werewolfGame.findPlayer(str(killed_user)).alive = False
            await die(ctx, killedPlayer)
            werewolfGame.killed = True
            winner = werewolfGame.findWinner()
            if winner == "werewolves":
                # town-square
                await bot.send_message(bot.get_channel(special_channels["town-square"]), "The werewolves outnumber the villagers. Werewolves win the game!")
            elif winner == "villagers":
                # town-square
                await bot.send_message(bot.get_channel(special_channels["town-square"]), "The werewolves are all dead. The villagers win!")
            elif winner == "lovers":
                # town-square
                await bot.send_message(bot.get_channel(special_channels["town-square"]), "We see that love prevails. The only two people alive are the lovebird. Cupid did a great job!!")
        else:
            await bot.say("Killing that person didn't work out. Maybe you mistyped, or maybe that person has already been killed. Please try again!")
