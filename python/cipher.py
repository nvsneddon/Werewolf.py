import random
from caesarcipher import CaesarCipher


class Cipher:

    def __init__(self, message: str):
        num = random.randint(1, 3)
        self.__message: str = message
        self.__jumbled_message: str = ""
        self.__hint: str = ""

        if num == 1:
            self.__caesarCipher()
        elif num == 2:
            self.__swapLetters()
        elif num == 3:
            self.__removeLetters()

    def __caesarCipher(self, ):
        i = random.randint(1, 25)
        self.__jumbled_message = CaesarCipher(self.__message, offset=i).decoded
        self.__hint = "Caeser Cypher {}".format(i)

    def __swapLetters(self):
        lst = list(self.__message)
        random.shuffle(lst)
        self.__hint = "Jumble"
        self.__jumbled_message = ''.join(lst)

    def __removeLetters(self):
        lst = list(self.__message)
        count = 0
        for i in range(len(lst)):
            if random.randint(1, 4) == 1:
                lst[i] = self.RandCharacter
                count += 1
        self.__hint = "Some letters are lost forever"
        if count < (len(lst) / 4):
            self.__removeLetters()
        else:
            self.__jumbled_message = ''.join(lst)

    @property
    def RandCharacter(self):
        return random.choice(('!', '@', '%', '#', '$', '&', '^', '*'))

    @property
    def Hint(self):
        return self.__hint

    @property
    def Message(self):
        return self.__message

    @property
    def Decode(self):
        return self.__jumbled_message


if __name__ == '__main__':
    x = Cipher("small")
    print(x.Decode)
    print(x.Hint)
    print(x.Message)
