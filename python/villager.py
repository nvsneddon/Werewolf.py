import models.villager
from exceptions import DocumentFoundException



class Villager:

    def __init__(self, discord_tag: str, character: str, id: int, nickname=None, server=0):
        # specialChannel = ("werewolf", "bodyguard", "seer", "cupid")
        self.__name: str = discord_tag.split("#")[0]
        self.__discordTag: str = discord_tag
        self.__nickname = nickname
        self.__character: str = character
        self.__is_werewolf: bool = (character == "werewolf")
        self.__killer: bool = (character == "werewolf" or character == "hunter")
        self.__alive: bool = True
        self.__inLove: bool = False
        self.__userID = id
        self.__protected = False
        self.__id = 0

        schema = {
            "name": discord_tag,
            "server": server,
            "character": character,
            "werewolf": self.__is_werewolf
        }
        # v = models.villager.Villager.find_one(schema)
        # if v is not None:
        #     raise DocumentFoundException
        v = models.villager.Villager(schema)
        v.save()

        # self.__inSpecialChannel = bool(character in specialChannel)

    @property
    def UserID(self) -> int:
        return self.__userID

    @property
    def Name(self):
        return self.__name

    @property
    def Protected(self):
        return self.__protected

    @property
    def DiscordTag(self):
        return self.__discordTag

    @property
    def Character(self):
        return self.__character

    @property
    def Dead(self) -> bool:
        return not self.__alive

    @property
    def CanKill(self) -> bool:
        return self.__killer

    @property
    def Mention(self) -> str:
        return "<@" + str(self.__userID) + ">"

    @property
    def NickName(self) -> str:
        return self.__nickname if self.__nickname is not None else ''

    @property
    def ProperName(self):
        return self.__nickname if self.__nickname is not None else self.__name

    @property
    def InLove(self):
        return self.__inLove

    @property
    def Werewolf(self) -> bool:
        return self.__is_werewolf

    @Protected.setter
    def Protected(self, value):
        self.__protected = value

    def die(self) -> bool:
        self.__alive = False
        return self.__is_werewolf

    def __str__(self):
        return f"Name: {self.__name}\nTag: {self.__discordTag}\nID: {self.__userID}\n" \
               f"Character: {self.__character}\nAlive: {self.__alive}\n" \
               f"Nickname: {self.__nickname if self.__nickname else 'No Nickname'}\n"

    def __eq__(self, other):
        if self is None or other is None:
            return False
        return self.__name == other.__name
