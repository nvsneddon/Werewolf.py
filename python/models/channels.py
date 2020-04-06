import json
import os

import mongothon

from dbconnect import my_db

channels_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "channels": {"type": dict}
})

Channels = mongothon.create_model(channels_schema, my_db["channels"])

if __name__ == "__main__":
    test = Channels({
        "server": 123456,
        "channels": {
            "town-square": 264,
            "yeah": 26
        }
    })
    test.save()
    x = Channels.find_one({"server": 123456})
    print(type(x['_id']))
    id_string = str(x['_id'])
    print(id_string)
    print(x)
    y = Channels.find_by_id(id_string)
    print("The thing is", y)
    x.remove()
    # test.save()


def getChannelId(channel: str, server) -> int:

    x = Channels.find_one({"server": server})
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
        x = Channels(channels)
        x.save()
    return x["channels"][channel]