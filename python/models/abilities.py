import mongothon

from dbconnect import my_db

ability_schema = mongothon.Schema({

})

Abilities = mongothon.create_model(ability_schema, my_db['abilities'])