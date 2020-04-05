import mongothon
import time

from schemer import ValidationException

from dbconnect import my_db

def set_day(guild_id, time_input):
    try:
        document = Server.find_one({"server": guild_id})
        if document is None:
            document = Server({
                "server": guild_id
            })
            document.save()
        time.strptime(time_input, '%H:%M')
        time_array = time_input.split(':')
        if int(time_array[0]) < 10 and len(time_array[0]) < 2:
            time_array[0] = "0" + time_array[0]
            document["daytime"] = ':'.join(time_array)
            document.save()
        else:
            document["daytime"] = time_input
            document.save()
        return True
    except ValueError:
        return False

def set_night(guild_id, time_input):
    try:
        document = Server.find_one({"server": guild_id})
        if document is None:
            document = Server({
                "server": guild_id
            })
            document.save()
        time.strptime(time_input, '%H:%M')
        time_array = time_input.split(':')
        if int(time_array[0]) < 10 and len(time_array[0]) < 2:
            time_array[0] = "0" + time_array[0]
            document["nighttime"] = ':'.join(time_array)
            document.save()
        else:
            document["nighttime"] = time_input
            document.save()
        return True
    except ValueError:
        return False

def set_warning(guild_id, minutes):
    document = Server.find_one({"server": guild_id})
    if document is None:
        document = Server({
            "server": guild_id
        })
        document.save()
    document["warning"] = int(minutes)
    try:
        document.save()
        return True
    except ValidationException:
        return False

def delete_many(filter):
    my_db['server'].delete_many(filter)

def time_format():
    def validate(value):
        try:
            time.strptime(value, '%H:%M')
            h, m = value.split(':')
            if int(h) < 10 and len(h) < 2:
                return "Invalid time format"
        except ValueError:
            return "Invalid time format"

    return validate


def validate_warning():
    def validate(value):
        if value > 180:
            return "Warning has to be within three hours of nighttime"

    return validate


server_schema = mongothon.Schema({
    "server": {"type": int, "required": True},
    "daytime": {"type": str, "default": "08:00", "validates": time_format()},
    "nighttime": {"type": str, "default": "20:00", "validates": time_format()},
    "warning": {"type": int, "default": 30, "validates": validate_warning()}
})

Server = mongothon.create_model(server_schema, my_db['server'])
