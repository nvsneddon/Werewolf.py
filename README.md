# Werewolf
This is a discord bot that narrates a game of real time werewolf, werewolf with a day/night cycle spanning 24 hours, giving an interesting twist on werewolf. The bot can narrate on its own without any input from anyone that's not playing the game. If you're just someone that's playing a game and want to know how real time werewolf works and how to use the bot as a player, you can [click here](./how-to-play.md)


## How to host a game
To host a game of real-time werewolf, you can invite the narrator bot to your server and the narrator will take care of most things. As the server owner or admin, you do have some responsibility 
to ensure that the game runs smoothly. The narrator responds to admin commands given to it from the bot-admin channel that it will create automatically when invited to a server.
The server owner can decide who can interact with the bot-admin channel by granting the appropriate permissions. 

### Setting up the server
The bot needs to do two things before it can start narrating games. 
1. Create the needed roles for the game
    * Alive
    * Dead
    * Playing
2. Create the channels for the town

You can do this with the command !setupserver. 

#### !setupserver

This command has two parts, creating the roles and creating the channels along with the town category. 
Creating the category requires the bot to have special permissions granted to it. You can run the !setupserver and it will do everything if you grant it administrative privileges temporarily. (You can ungrant the admin privileges as soon as it's done setting up the server). 

If you do not want to grant the bot admin privileges, you can still run the !setupserver command and it will set up as much as it can on its own. Afterwards, you need to manually set up the permissions for the narrator in the town category. The bot will need the following permissions in the category "The Town":
* Manage Channel
* Manage Permissions
* Read Text Channels & see Voice Channels
* Send messages
* Manage Messages
* Read Message History

Once the bot has those permissions granted in the town category, you can use the !setupserver command to finish where you started off and the bot will set up the channels it needs to run the game.

Once the server has been set up, you can start a game of werewolf.


### Managing time
Because this is real time, there are set times every day for the nighttime phase to start and the daytime phase to start.
To get the current settings, use the !gettime command. If you wish to change the time, you can use the !changeday/changenight command in the bot-admin channel.
If you use !changeday 9:00 it will change the day to 9:00 am Mountain Standard Time (The location of the server hosting the bot). 
Time zone support will be available soon. 
There is a warning that is given 30 minutes before nighttime falls that can be adjusted as well. You can use !changewarning command to set the number of minutes before nighttime the warning will be set.
As of right now, these settings cannot be changed mid game, though that will likely change as soon as I can figure out a good way to implement it.

### Starting a game
Everyone that wants to play must have the playing role assigned to them. They can use the !playing command to say that they are playing. 
Once you have enough people and everyone is ready to start a game, you can use the !startgame command to start a game.
You'll need to specify how many players of each role there will be. You can do this by listing the numbers after invoking the command. 
The order of roles that you specify are: werewolves, seers, bodyguards, cupids, hunters, bakers, and masons.
Starting a game with two werewolves, two masons, and one of each other character would look like this:

!startgame 2 1 1 1 1 1 2

If you wish to leave out any role, you can use 0 or, if no other number follows, leave it blank. 

For example: !startgame 3 1 1 0 1 will start a game with 3 werewolves, 1 seer, 1 bodyguard, no cupids, 1 hunter, and no bakers or masons.

The seers, bodyguards, and baker roles are best kept to one per match, but feel free to experiment with other combinations of players.

#### Suggestions about what roles to use.
Bakers are to be used when there are many people in the game as the baker will cause more deaths and make more people die. If there are more than 12 people, it would help speed things up.
Masons are very powerful, so they are best used when there is also a baker to help balance the game out. With masons, werewolves tend to die quickly, however very good and deceiving dead werewolves can sabotage the masons.

### Ending a game

If you need to end a game before it's finished, simply use the !endgame command. Be aware that this will erase all progress of the current game.  


### Playing along with everyone else
One limitation of discord is that, no matter what permissions you grant the owner, they will always be able to see every channel, meaning that the owner cannot 
play a fair game with everyone else. The workaround that I did with this is make a second discord account so that you can transfer ownership to that account and so that way you can play the game as well.
You can grant your account access to bot-admin and you'll still be able to start/end games as you need. 



### FAQs
* Why does the bot need admin permissions to create the town square channels?

Good question. It's because the channels for the werewolf game have special permissions to keep people who are playing the game from seeing who the werewolves, seer, 
bodyguard, etc are. When the game goes, everyone that is alive cannot see the channels that they aren't specifically invited to. They'll be invited to the channels
that correspond to their role (Werewolves will get access to the werewolf channel, seers to the seer channel, etc.) Because by default, these channels are restricted
the narrator bot has to mark its role as an exception to those restrictions so that the narrator can narrate as expected. If you want to set up the permissions for the channel category "The Town" yourself, you can follow the instructions [here](#setupserver) and you'll never have to grant the narrator admin privileges. 



### Contributing
Contributions are very welcome. 
[Click here](CONTRIBUTE.md) to learn how to contribute to this project.
