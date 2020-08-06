## logs/

This directory holds various log files created by the running Evennia
server. It is also the default location for storing any custom log
files you might want to output using Evennia's logging mechanisms.
It is created here so you won't have to make it manually on first-run.

Some logs you may see here are:
portal.log - network connections into the portal.
http_requests.log -  generated when debugging web.
lockwarnings.log - documents object lock changes in-world.
server.log - server events.
channel_<name>.log - messages sent on channel when logging is on.

Logs are rotated when they reach 1 MB in size.