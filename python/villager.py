class Villager:
    def __init__(self, discordtag, character):
        # specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__name = discordtag.split("#")[0]
        self.__discordTag = discordtag
        self.__character = character
        self.__werewolf = (character == "werewolf")
        self.__killer = (character == "werewolf")
        self.__alive = True
        self.__protected = False
        self.__usedAbility = False
        self.__inLove = False
        # self.__inSpecialChannel = bool(character in specialChannel)

    def getName(self):
        return self.__name
    
    def getDiscordTag(self):
        return self.__discordTag

    def getCharacter(self):
        return self.__character

    def protect(self):
        self.__protected = True

    def die(self) -> None:
        self.__alive = False

    def isDead(self) -> bool:
        return not self.__alive

    def isWerewolf(self) -> bool:
        return self.__werewolf

    def isKiller(self) -> bool:
        return self.__killer

    def isProtected(self) -> bool:
        return self.__protected

    def __str__(self):
        return "Name: {}\nTag: {}\nCharacter: {}\nAlive: {}".format(self.__name, self.__discordTag, self.__character, self.__alive)

    def __eq__(self, other):
        return self.__name == other.__name
    
    def findPlayer(self, ctx, name: str):
        if name[0:3] == "<@!":
            return ctx.message.server.get_member(name[3:-1])
        elif name[0:2] == "<@":
            return ctx.message.server.get_member(name[2:-1])
        else:
            return ctx.message.server.get_member_named(name)
