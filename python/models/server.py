import mongothon
import time

from dbconnect import my_db


def time_format():
    def validate(value):
        try:
            time.strptime(value, '%H:%M')
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
