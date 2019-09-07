class Villager:
    def __init__(self, discordtag: str, character: str, id: int):
        # specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__name: str = discordtag.split("#")[0]
        self.__discordTag: str = discordtag
        self.__character: str = character
        self.__werewolf: bool = (character == "werewolf")
        self.__killer: bool = (character == "werewolf")
        self.__alive: bool = True
        self.__usedAbility: bool = False
        self.__inLove: bool = False
        self.__userID = id
        # self.__inSpecialChannel = bool(character in specialChannel)

    def getUserID(self) -> int:
        return self.__userID

    def getName(self):
        return self.__name
    
    def getDiscordTag(self):
        return self.__discordTag

    def getCharacter(self):
        return self.__character

    def die(self) -> None:
        self.__alive = False

    def isDead(self) -> bool:
        return not self.__alive

    def isWerewolf(self) -> bool:
        return self.__werewolf

    def isKiller(self) -> bool:
        return self.__killer
    
    def __str__(self):
        return "Name: {}\nTag: {}\nID: {}\nCharacter: {}\nAlive: {}".format(self.__name, self.__discordTag, str(self.__userID), self.__character, self.__alive)

    def __eq__(self, other):
        if self is None or other is None:
            return False
        return self.__name == other.__name
    