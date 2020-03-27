import mongothon

time_schema = mongothon.Schema({"hour": {"type": int, "required": True}, "minute": {"type": int, "required": True}})
server_schema = mongothon.Schema({
    "server_id": {"type": int, "required": True},
    "daytime": {"type": time_schema, "required": True},
    "nighttime": {"type": time_schema, "required": True}
})
