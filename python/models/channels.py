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