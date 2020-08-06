# Welcome to Novel Online World!![Pangolin in motion](https://github.com/Pinacolada64/NOW/blob/master/web/static/website/images/NOW-icon.png)

This directory is the directory that contains the NOW assets in
development, and does not actually mirror the operating NOW server.

If you are cloning NOW, be aware that this is the customized code
in development, and not the full code for the server.

The prerequisite install of the latest Evennia is required. Be aware
that NOW runs atop Evennia in a separate game folder named NOW.

# Getting started with Evennia's install

It's highly recommended that you look up Evennia's extensive
documentation found here: https://github.com/evennia/evennia/wiki.

Plenty of beginner's tutorials can be found here:
http://github.com/evennia/evennia/wiki/Tutorials.

After the full install of Evennia, outside the evennia folder,
while operating the pyenv as directed by Evennia's install
and operation proceedure, before installing this game code,

    evennia --init NOW

 If you have no existing database for your game, `cd NOW` then
 initialize a new database using:

    evennia migrate

To start the server, `cd` to this directory and run

    evennia -i start

You will see console output, but can disconnect with Control-D or exit.
Evennia stays running in daemon mode and displays output to the console.

Make sure to create a superuser when asked. By default you can now
connect using a MUD client on localhost:4000.  You can also use 
the web client by pointing a browser to

    http://localhost:8000

Within it is the game's main configuration file, Evennia will
create a default configuration file; you don't need to change
it to get started): `NOW/server/conf/settings.py`
