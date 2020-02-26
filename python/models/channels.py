import mongothon

from models.dbconnect import my_db

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
    # x = Channels.find_one({"server": 123456})
    # x.remove()
    # test.save()