import json
import os
import bot

def main():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../config/messages.json')

    try:
        f = open(filename)
        werewolfMessages = json.loads(f.read())
        f.close()
        print('\n'.join(werewolfMessages["werewolf"]["welcome"]))
        """f2 = open("command_descriptions.json")
        commandDescriptions = json.loads(f2.read())
        f2.close()
        f3 = open("channels.json")
        special_channels = json.loads(f3.read())
        f3.close()"""
    except FileNotFoundError:
        print("File not found")
    except:
        print("Something else went wrong")

    test = bot.Bot()

main()