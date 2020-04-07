# Werewolf
This is like the werewolf bot I built for discord, except more modular and open source. 
The point of this project is to open source the werewolf bot and make it available to the world.

### discord-config.json
In this project, you will see a discord-config_example.json file. This is just an example file for how the discord-config.json file should look like.
When the bot runs and doesn't find the discord-config.json file, it will walk you through steps to generate the file.

If you want to make the file manually, you can rename the discord-config_example.json file to discord-config.json and replace the fields with your configurations. 


### Creating the token and deploying the bot
To get the discord bot working, you will need to set up your own bot and get your own token at https://discordapp.com/developers/applications/. Create an application and then build the bot. 
Once the bot has been registered, you will be able to receive a token. On that page, you can go to oauth2 and select bot under scopes to get an invite link for the bot to join your server.

### Permissions
The permissions needed to run the bot is administrator for now. This will change as I test this more and find what permissions are needed/not needed. 
If anyone would like to let me know what permissions worked, please feel free to send me an email.

### After bot invite
Once the bot is on your server and running, you will see a bot-admin channel. If this did not get created, please let me know and I'll make sure that bug is sorted out.
The bot-admin channel is to run the bot on your server.

#### Set up
To get the server to have the appropriate roles and channels, please run the following command.
!addroles (This will add the dead, alive, playing, notplaying roles)
!addcategory (Adds the town category as well as all channels for werewolf)

After that, you can use the command to !startgame


### Contributing
Contributions are very welcome. 
[Click here](CONTRIBUTE.md) to learn how to contribute to this project.
