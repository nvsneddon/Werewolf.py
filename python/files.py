import json
import os
from datetime import datetime
import models.channels

dirname = os.path.dirname(__file__)
try:
    f = open(os.path.join(dirname, '../config/messages.json'))
    werewolfMessages = json.loads(f.read())
    f.close()
    f2 = open(os.path.join(dirname, "../config/command_descriptions.json"))
    commandDescriptions = json.loads(f2.read())
    f2.close()
except FileNotFoundError:
    print(
        "Please make sure the messages.json and the command_descriptions.json files are in the config folder and try "
        "again.")
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
    minutes_before_warning = int(input())
    warn_voting_time = datetime(1, 1, 1, int(
        config['nighttime'][:2]), int(config['nighttime'][3:5])) - datetime(1, 1, 1, 0, minutes_before_warning)
    # config['vote-warning'] = str(warn_voting_time)[:5]
    config['minutes-before-warning'] = minutes_before_warning
    print("Voter warning is", str(warn_voting_time)[:5])
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

try:
    with open(os.path.join(dirname, '../config/commands.json')) as f6:
        command_parameters = json.loads(f6.read())
except FileNotFoundError:
    print("No comamnds.json file found.")
    exit()

def writeJsonToConfig(filename: str, file: dict) -> None:
    writeToConfig(filename, json.dumps(file))


def writeToConfig(filename: str, file: str) -> None:
    try:
        dir_name = os.path.dirname(__file__)
        f = open(os.path.join(dir_name, '../config/' + filename), "w")
        f.write(file)
        f.close()
    except:
        print("Something went wrong with writing the file")

def isBad(character: str):

    character_dict = readJsonFromConfig("characters.json")
    return character in character_dict["bad"]


def readFromConfig(filename: str) -> str:
    try:
        dir_name = os.path.dirname(__file__)
        f = open(os.path.join(dir_name, "../config/" + filename))
        readfile = f.read()
        f.close()
        return readfile

    except FileNotFoundError:
        print("File " + filename + " not found")
        raise FileNotFoundError


def readJsonFromConfig(filename: str) -> dict:
    return json.loads(readFromConfig(filename))


def fileFoundInConfig(filename: str) -> bool:
    dir_name = os.path.dirname(__file__)
    return os.path.exists(os.path.join(dir_name, "../config/" + filename))

#
# def get_channel_ids() -> dict:
#     try:
#         dir_name = os.path.dirname(__file__)
#         f = open(os.path.join(dir_name, "../config/channel_id_list.json"))
#         readfile = json.loads(f.read())
#         f.close()
#         return readfile
#
#     except:
#         return {}


def getChannelId(channel: str, server=681696629224505376) -> int:

    x = models.channels.Channels.find_one({"server": server})
    if x is None:
        dir_name = os.path.dirname(__file__)
        f = open(os.path.join(dir_name, "../config/channel_id_list.json"))
        channels = {}
        channels["channels"] = {}
        channels["server"] = server
        read_file = json.loads(f.read())
        for x, y in read_file.items():
            if x == "guild":
                continue
            channels["channels"][x] = y
        f.close()
        x = models.channels.Channels(channels)
        x.save()
    return x["channels"][channel]
