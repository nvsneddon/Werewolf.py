import mongothon

from dbconnect import my_db

def delete_many(filter):
    my_db['elections'].delete_many(filter)

election_schema = mongothon.Schema({
    "server": {"type": str, "required": True},
    "people": {"type": list, "required": True},
    "channel": {"type": str, "required": True},
    "casted_votes": {"type": dict, "default": {}},
    "voted": {"type": dict, "default": {}},
    "locked": {"type": list, "default": []},
    "lynch": {"type": bool, "default": True}
})

Election = mongothon.create_model(election_schema, my_db["elections"])
