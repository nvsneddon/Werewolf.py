class Villager:

    def __init__(self, discordtag: str, character: str, id: int):
        # specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__name: str = discordtag.split("#")[0]
        self.__discordTag: str = discordtag
        self.__character: str = character
        self.__is_werewolf: bool = (character == "werewolf")
        self.__killer: bool = (character == "werewolf" or character == "hunter")
        self.__alive: bool = True
        self.__usedAbility = False
        self.__inLove: bool = False
        self.__userID = id
        # self.__inSpecialChannel = bool(character in specialChannel)

    @property
    def UserID(self) -> int:
        return self.__userID

    @property
    def UsedAbility(self):
        return self.__usedAbility

    @property
    def Name(self):
        return self.__name
    
    @property
    def DiscordTag(self):
        return self.__discordTag

    @property
    def Character(self):
        return self.__character

    @property
    def isDead(self) -> bool:
        return not self.__alive

    @property
    def CanKill(self) -> bool:
        return self.__killer

    @property
    def IsWerewolf(self) -> bool:
        return self.__is_werewolf

    def useAbility(self):
        self.__usedAbility = False

    def die(self) -> None:
        self.__alive = False

    def __str__(self):
        return "Name: {}\nTag: {}\nID: {}\nCharacter: {}\nAlive: {}".format(self.__name, self.__discordTag, str(self.__userID), self.__character, self.__alive)

    def __eq__(self, other):
        if self is None or other is None:
            return False
        return self.__name == other.__name
    