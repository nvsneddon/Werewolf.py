import mongothon

from dbconnect import my_db

election_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "people": {"type": list, "required": True},
    "future": {"type": object, "required": True},
    "channel": {"type": int, "required": True},
    "casted_votes": {"type": dict, "default": {}},
    "voted": {"type": dict, "default": {}},
    "locked": {"type": list, "default": []}
})

Election = mongothon.create_model(election_schema, my_db["elections"])