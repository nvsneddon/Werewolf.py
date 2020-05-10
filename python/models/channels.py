import json
import os

import mongothon

from dbconnect import my_db

channels_schema = mongothon.Schema({
    "server": {"type": str, "required": True},
    "channels": {"type": dict}
})

Channels = mongothon.create_model(channels_schema, my_db["channels"])

def getChannelId(channel: str, server) -> int:

    x = Channels.find_one({"server": str(server)})
    if x is None:
        dir_name = os.path.dirname(__file__)
        f = open(os.path.join(dir_name, "../config/channel_id_list.json"))
        channels = {}
        channels["channels"] = {}
        channels["server"] = str(server)
        read_file = json.loads(f.read())
        for x, y in read_file.items():
            if x == "guild":
                continue
            channels["channels"][x] = y
        f.close()
        x = Channels(channels)
        x.save()
    return int(x["channels"][channel])