import mongothon

from dbconnect import my_db

def delete_many(filter):
    my_db['elections'].delete_many(filter)

election_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "people": {"type": list, "required": True},
    "channel": {"type": int, "required": True},
    "casted_votes": {"type": dict, "default": {}},
    "voted": {"type": dict, "default": {}},
    "locked": {"type": list, "default": []},
    "lynch": {"type": bool, "default": True}
})

Election = mongothon.create_model(election_schema, my_db["elections"])

# x = Channels.find_one({"server": 123456})

if __name__ == "__main__":
    test = Election({
        "server": 163,
        "people": ["hi", "what", "is"],
        "channel": 163263523
    })
    test.save()
    x = Election.find_one({"server": 163})
    print(type(x['_id']))
    id_string = str(x['_id'])
    print(id_string)
    x["people"].append("wow!")
    print(x)
    x.save()
    y = Election.find_by_id(id_string)
    print("The thing is", y)
    x.remove()
    # test.save()