## How to use the narrator
The prefix of the narrator is ! for every other command. 
To get help, simply type !help or !help command for help on a specific command. 

More on how to use the narrator will be given with how to play.

## How to play

If you don't know how to play werewolf, you can go to this [link](https://www.playwerewolf.co/rules) to get the basic idea of how to play the game.
This version of werewolf runs a bit differently, as the daytime/nighttime cycle takes 24 hours, making this a more realistic feeling version of werewolf.

## How to host the game
To host the game, you can invite the narrator bot to your server and the narrator will take care of most things. As the server owner or admin, you do have some responsibility 
to ensure that the game runs smoothly. The narrator responds to admin commands given to it from the bot-admin channel that it will create automatically when invited to a server.
The server owner can decide who can interact with the bot-admin channel by granting the appropriate permissions. 

### Setting up the server
The bot needs to do two things before it can start narrating games. 
1. Create the needed roles for the game with !addroles
    * Alive
    * Dead
    * Playing
2. Create the channels for the town with !addchannels
(Side note, this command needs admin permission right now. You can find a full explanation [here](#FAQS))

Once those things have been done, you can start a game

## For players

To use the narrator, you can invoke the bot using the ! prefix. Try out using !ping and see it give you a response. 

### Playing the game
To play a round, please mark yourself as playing using the !playing command. You can be sure that you're playing when the narrator tells you that you're playing
and when your names turns yellow. When the game starts, you'll get a DM stating what your role is and what your objective is. 

### Roles of werewolf

##### Villager
Villagers are normal everyday people with no special ability.

##### Werewolves
Werewolves pretend to be villagers, but they discuss in the #werewolves channel whom they should kill at night. They can use the !kill command to kill anyone.
If they want to kill John doe with the discord name jdoe#2521 and the nickname John, they can either type jdoe, jdoe#2521, or John. Mentioning people is hard as they cannot be mentioned in a channel that they don't have access to.
The bot is not case sensitive, so !kill John and !kill john will kill the same person.

##### Seer
The seer can investigate someone once per night by using the !investigate commmand. They can either use the discord user name with or without the discriminator, or use the nickname. 

##### Bodyguard
Once per day/night cycle, the bodyguard can protect someone using !protect person. The power restarts every time day starts and can only be used once during that cycle.

##### Cupid/Lovebirds
Cupid has the power to make two people fall in love using !match person1 person2. Once those people are in love, their fates are tied together. 
If one of them dies, so will the other. The lovebirds won't know who set them up and will try to be the last two people alive in the game.

##### Hunter
The hunter is an ordinary villager with a killer final shot. Once the hunter dies, the hunter will be able to shoot any person they desires using the !shoot person command.
The hunter does not have their own channel. They shoot their target in town square and publically announce who they shoot. 

##### Baker
The baker has no special ability but instead devotes their time to baking delicious bread for everyone. Once the baker dies, people will start dying of starvation (unless they're a werewolf because they eat humans).
Every day, up to three villagers will die of starvation until the werewolves win. If you're the baker, do your best not to get killed.

##### Masons
The masons are a secret group of people that know who each other are. They know that they aren't masons, so you can trust them (unless one of them is in love with a werewolf). 
They also receive messages from the dead every night. These are one worded clues that can help the masons. However, the dead werewolves can also send a message, so the masons have to find out what message is trustworthy
and which message isn't. 

##### Dead people
Even if you're dead, you're still in the game. You can see everything happening, but you can't interact directly with any of the game channels. 
You have a goal to help the masons get closer to know who the werewolf is. You can send them a message every night. Dead werewolves can also send one message every night
to try and throw the masons off. These messages can be sent in the afterlife channel using the !sendmessage command. You can send a message with the word short as follows:
!sendmessage short
The masons can get up to two messages per night, one from the dead werewolves and one from the dead masons.  

### Win conditions
There are three win conditions
* Werewolves win when there are more werewolves than villagers. Note that 4 villagers to 4 werewolves doesn't yet secure a win for the werewolves.
* Villagers win when every werewolf is dead
* The two lovebirds and cupid win when the two love birds are the last two people alive. (That means that both of them should work together to survive even when the love birds are on different teams.)
###

## For server admins

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

Good question. It's because the channels have special permissions to keep people who are playing the game from seeing who the werewolves, seer, 
bodyguard, etc are. When the game goes, everyone that is alive cannot see the channels that they aren't specifically invited to. They'll be invited to the channels
that correspond to their role (Werewolves will get access to the werewolf channel, seers to the seer channel, etc.) Because by default, these channels are restricted
the narrator bot has to mark its role as an exception to those restrictions so that the narrator can narrate as expected. The problem is that no bot without administrator rights
can make that grant itself an exception to channel permissions, even with every other permission was granted. My current working solution to deploy the bot without having to give admin privileges is to 
only ask for the admin permissions before running this command. That way you don't have to worry about the narrator doing stuff you don't want it to.
If someone can find a way to get this to work without admin permissions, please let me know. I'd love to find a good working solution around this problem.

