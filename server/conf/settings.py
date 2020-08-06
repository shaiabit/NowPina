"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/NOW/NOWMU/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

SERVERNAME = 'NOW'

TELNET_PORTS = [4000]

WEBSERVER_PORTS = [(8000, 8001)]

IDMAPPER_CACHE_MAXSIZE = 150  # Keeping cache size small for now

INLINEFUNC_ENABLED = False  # Needs testing before use.

IDLE_TIMEOUT = 5 * 60 * 60  # 5 hours

DELAY_CMD_LOGINSTART = 0.6

MULTISESSION_MODE = 1

IRC_ENABLED = True  # @irc2chan Public = irc.furnet.org 7000 #NOW NOW

SSH_ENABLED = True  # Activate SSH protocol communication (SecureShell)

SSH_PORTS = [3699]  # Ports to use for SSH

SSL_ENABLED = True  # Activate Telnet+SSL protocol (SecureSocketLibrary) for supporting clients

SSL_PORTS = [8888]  # Ports to use for Telnet+SSL

IN_GAME_ERRORS = False  # Errors in console are sufficient.

SEARCH_MULTIMATCH_REGEX = r'(?P<number>[0-9]+) (?P<name>.*)'
SEARCH_MULTIMATCH_TEMPLATE = ' {number} {name}{aliases}{info}\n'
COMMAND_DEFAULT_ARG_REGEX = r'^[ /]+.*$|$'

ENCODINGS = ['utf-8', 'latin-1', 'ISO-8859-1', 'cp437']

######################################################################
# Account settings
######################################################################

# The default permission given to all new accounts
PERMISSION_ACCOUNT_DEFAULT = 'denizen'

HELP_MORE = False
PERMISSION_HIERARCHY = ['Guest',      # NOTE: only used if GUEST_ENABLED=True
                        'Denizen',    # Player
                        'Citizen',    #
                        'Helper',     # Helper
                        'Crafter',    #
                        'Builder',    # Builder
                        'Helpstaff',  #
                        'Mage',       #
                        'Wizard',     # Admin
                        'Immortal']   # Developer

######################################################################
# In-world settings
######################################################################
# Room settings
######################################################################
HOME_ROOM_DESC = 'You may |gdesc/room ...|n to change it, and ' \
                 'you can review |gcolor ansi|n to add effects ' \
                 'to spruce it up.|/|/|nYou can always type ' \
                 '|groom|n to get back here and can invite folks ' \
                 'over with |gsummon|n.|/Have other questions? ' \
                 'Use |ghelp|n with only the 1st word of each of those.'
# Other settings
######################################################################
WELCOME_URL = 'http://lazylion.ddns.net:8000/static/website/images/nowlogo.png'
WELCOME_TEXT = ('''
        |rN  N |y  OOO |g W   W
        |rNN  N|y OO OO|g W   W
        |rN N N|y O   O|g W W W
        |rN  NN|y OO OO|g W W W
        |r N  N|y  OOO |g  W W
         ''', 'NOW (in large friendly letters)')
ABOUT_TEXT = 'NOW is an alpha build mu* made possible by early adopters, ' \
             'testers, and designers who show up regularly, and believe.'
QUIT_MESSAGE = 'Hope to see you again, soon!' \
               '|/A survey is available at http://nowsurvey.supernormality.net/ for your thoughts'
NOTHINGNESS = '|=zNo|=wth|=min|=jgn|=ies|=ds|n'
RAINBOW = '|Rr|430a|yi|Gn|bb|co|mw'
APPLE = '|r((|g`|r)|n'
