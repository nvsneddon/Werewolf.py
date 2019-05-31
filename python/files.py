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
except FileNotFoundError:
    print("Please make sure the messages.json and the command_descriptions.json files are in the config folder and try again.")
    exit()
try:
    f3 = open(os.path.join(dirname, "../config/discord-config.json"))
    config = json.loads(f3.read())
    f3.close()
except FileNotFoundError:
    print("The config file was not found. Please make sure the discord-config.py file is in the config folder. Please refer to the README for more information.")
    exit()
try:
    f4 = open(os.path.join(dirname, "../config/channels-config.json"))
    channels_config = json.loads(f4.read())
    f4.close()
except FileNotFoundError:
    print("The channels-config.json file was not found and could not be loaded")
    exit()