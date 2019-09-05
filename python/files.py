import os
import json
from datetime import datetime, time

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
    print("Please enter your token:")
    config = dict()
    config['token'] = str(input())
    print("What time should day start? (Format hh:mm in 24h format. 8 pm would be 20:00, and 6 am would be 06:00):")
    config['daytime'] = str(input())
    print("What time should night start? (Format hh:mm in 24h format. 8 pm would be 20:00, and 6 am would be 06:00):")
    config['nighttime'] = str(input())
    print("How many minutes before the voting closes do you want to issue a warning?:")
    minutesbeforewarning = eval(input())
    warnvotingtime = datetime(1, 1, 1, eval(
        config['nighttime'][:2])) - datetime(1, 1, 1, 0, minutesbeforewarning)
    config['vote-warning'] = str(warnvotingtime)[:5]
    config['minutes-before-warning'] = minutesbeforewarning
    print("Voter warning is ", config['vote-warning'])
    f3 = open(os.path.join(dirname, "../config/discord-config.json"), "w")
    f3.write(json.dumps(config))
    f3.close()
    print("You can change these settings later in the discord-config.json file found in the config folder.")
try:
    f4 = open(os.path.join(dirname, "../config/channels-config.json"))
    channels_config = json.loads(f4.read())
    f4.close()
except FileNotFoundError:
    print("The channels-config.json file was not found and could not be loaded")
    exit()
try:
    f5 = open(os.path.join(dirname, "../config/roles-config.json"))
    roles_config = json.loads(f5.read())
    f5.close()
except FileNotFoundError:
    print("The roles-config.json file was not found and could not be loaded")
    exit()


def writeJsonToConfig(filename: str, file: dict) -> None:
    writeToConfig(filename, json.dumps(file))

def writeToConfig(filename: str, file: str) -> None:
    try:
        dirname = os.path.dirname(__file__)
        f = open(os.path.join(dirname, '../config/' + filename), "w")
        f.write(file)
        f.close()
    except:
        print("Something went wrong with writing the file")

def readFromConfig(filename: str) -> str:
    try:
        dirname = os.path.dirname(__file__)
        f = open(os.path.join(dirname, "../config/" + filename))
        readfile = f.read()
        f.close()
        return readfile
        
    except:
        print("File " + filename + " not found")

def readJsonFromConfig(filename: str) -> dict:
    return json.loads(readFromConfig(filename))

def fileFoundInConfig(filename: str) -> bool:
    dirname = os.path.dirname(__file__)
    return os.path.exists(os.path.join(dirname, "../config/" + filename))