import mongothon

from dbconnect import my_db

def valid_hour():
    def validate(value):
        if value < 0 or value >= 24:
            return "Hour must be between 0 and 23"

    return validate


def valid_minute():
    def validate(value):
        if value >= 60 or value < 0 or value % 15 != 0:
            return "Minute can only be 0, 15, 30, or 45"

    return validate


time_schema = mongothon.Schema({"hour": {"type": int, "required": True, "validates": valid_hour()},
                                "minute": {"type": int, "required": True, "validates": valid_minute()}})
server_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "daytime": {"type": time_schema, "required": True},
    "nighttime": {"type": time_schema, "required": True}
})

Server = mongothon.create_model(server_schema, my_db['server'])
