# -*- coding: utf-8 -*-
"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.
"""

# [Default commands modules]
from evennia import default_cmds
# Use Evennia default commands in account group
from evennia.commands.default.account import CmdIC
from evennia.commands.default.account import CmdOOC
from evennia.commands.default.account import CmdPassword
from evennia.commands.default.account import CmdCharCreate
from evennia.commands.default.account import CmdOption
from evennia.commands.default.account import CmdSessions
from evennia.commands.default.account import CmdColorTest
# from evennia.commands.default.account import CmdQuell
#
# Use Evennia default commands in admin group
from evennia.commands.default.admin import CmdBoot
from evennia.commands.default.admin import CmdBan
from evennia.commands.default.admin import CmdUnban
from evennia.commands.default.admin import CmdEmit
from evennia.commands.default.admin import CmdNewPassword
from evennia.commands.default.admin import CmdPerm
#
# Use Evennia default commands in system group
from evennia.commands.default.system import CmdAccounts
from evennia.commands.default.system import CmdReload
from evennia.commands.default.system import CmdReset
from evennia.commands.default.system import CmdPy
from evennia.commands.default.system import CmdScripts
from evennia.commands.default.system import CmdObjects
from evennia.commands.default.system import CmdService
from evennia.commands.default.system import CmdServerLoad
from evennia.commands.default.system import CmdShutdown
from evennia.commands.default.system import CmdTickers
# [Default commands modules replacements]
# from commands import account   # Use Evennia default commands in account group
from commands import admin     # Use Evennia default commands in admin group
from commands import building  # Use Evennia default commands in building group
from commands import prelogin  # Use Evennia default commands in prelogin group

# from world.rpsystem import CmdSdesc, CmdEmote, CmdRecog, CmdMask  # RP commands used to be here.
from evennia.contrib.mail import CmdMail
from world.clothing import CmdWear, CmdRemove, CmdCover, CmdUncover, CmdGive

# [Traversal of path-exits]
from typeclasses.exits import CmdStop, CmdContinue, CmdBack, CmdSpeed

# [commands modules]
from commands.say import CmdSay, CmdOoc, CmdSpoof
from commands.who import CmdWho
from commands.desc import CmdDesc
from commands.flag import CmdFlag
from commands.home import CmdHome
from commands.menu import CmdMenu
from commands.page import CmdPage
from commands.pose import CmdPose
from commands.quit import CmdQuit
from commands.verb import CmdTry
from commands.zeit import CmdTime
from commands.zone import CmdZone
from commands.about import CmdAbout
from commands.mydie import CmdRoll
from commands.staff import CmdWall
from commands.staff import CmdAudit
from commands.sense import CmdSense
from commands.change import CmdChange
from commands.portal import CmdPortal
from commands.access import CmdAccess
from commands.account import CmdQuell
from commands.whisper import CmdWhisper
from commands.channel import CmdChannels
from commands.inventory import CmdInventory
from commands.prelogin import CmdUnconnectedAbout


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands available to
    in-world Character objects. It is merged with the `AccountCmdSet` when
    an Account puppets a Character.
    """
    key = 'DefaultCharacter'

    def at_cmdset_creation(self):
        """Populates the DefaultCharacter cmdset"""

        super(CharacterCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdGet)        # Replaced with custom version
        self.remove(default_cmds.CmdSay)        # Replaced with custom version
        self.remove(default_cmds.CmdDrop)       # Removed - replaced with lock action
        self.remove(default_cmds.CmdGive)       # Now handled by world/clothing
        self.remove(default_cmds.CmdLook)       # Now handled by sense command, along with 4 other senses
        self.remove(default_cmds.CmdPose)       # Replaced with custom version
        self.remove(default_cmds.CmdTime)       # Moved to account command
        self.remove(default_cmds.CmdAbout)      # Replaced with custom version
        self.remove(default_cmds.CmdAccess)     # Replaced with custom version
        self.remove(default_cmds.CmdSetHome)    # Replaced with home/set and home/here
        self.remove(default_cmds.CmdSetDesc)    # Duplicate subset of functions to CmdDesc
        self.remove(default_cmds.CmdDestroy)    # Reuse instead of destroy database objects.
        self.remove(default_cmds.CmdTeleport)   # Replaced with a Teleport that has cost and conditions.
        try:
            self.remove(default_cmds.CmdDelAccount)  # Disable instead of remove accounts.
# I don't think this actually exists.
        except:
            pass
# [...] Administrative commands:
        self.add(CmdBoot(locks='cmd:perm(boot) or perm(helpstaff)', help_category='Administration'))
        self.add(CmdBan(locks='cmd:perm(ban) or perm(immortal)', help_category='Administration'))
        self.add(CmdEmit(locks='cmd:perm(emit) or perm(helpstaff)', help_category='Administration'))
        self.add(CmdNewPassword(locks='cmd:perm(newpassword) or perm(wizard)', help_category='Administration'))
        self.add(CmdPerm(locks='cmd:perm(perm) or perm(immortal)', help_category='Administration'))
        self.add(CmdUnban(locks='cmd:perm(unban) or perm(immortal)', help_category='Administration'))
        self.add(CmdWall)
# [...] Building commands:
        self.add(building.CmdSetObjAlias)
        self.add(building.CmdCopy)
        self.add(building.CmdCpAttr)
        self.add(building.CmdMvAttr)
        self.add(building.CmdDig)
        self.add(building.CmdTunnel)
        self.add(building.CmdLink)
        self.add(building.CmdUnLink)
        self.add(building.CmdListCmdSets)
        self.add(building.CmdName)
        self.add(building.CmdOpen)
        self.add(building.CmdSetAttribute)
        self.add(building.CmdTypeclass)
        self.add(building.CmdWipe)
        self.add(building.CmdLock)
        self.add(building.CmdExamine)
        self.add(building.CmdFind)
        self.add(building.CmdScript)
        self.add(building.CmdTag)
        self.add(building.CmdSpawn)
# [...] System commands:
        self.add(CmdReload(locks='cmd:perm(reload) or perm(immortal)', help_category='System'))
        self.add(CmdReset(locks='cmd:perm(reset) or perm(immortal)', help_category='System'))
        self.add(CmdShutdown(locks='cmd:perm(shutdown) or perm(immortal)', help_category='System'))
        self.add(CmdAccounts(locks='cmd:perm(accounts) or perm(wizard)', help_category='Administration'))
        self.add(CmdObjects(locks='cmd:perm(objects) or perm(builder)', help_category='Building'))
        self.add(CmdPy(locks='cmd:perm(py) or perm(immortal)', help_category='System'))
        self.add(CmdScripts(locks='cmd:perm(scripts) or perm(wizard)', help_category='System'))
        self.add(CmdServerLoad(locks='cmd:perm(load) or perm(immortal)', help_category='System'))
        self.add(CmdService(locks='cmd:perm(service) or perm(immortal)', help_category='System'))
        self.add(CmdTickers(locks='cmd:perm(tickers) or perm(builder)', help_category='Building'))
# [...] Custom commands:
        self.add(CmdOoc)
        self.add(CmdSay)
        self.add(CmdTry)
        self.add(CmdDesc)
        self.add(CmdFlag)
        self.add(CmdGive)
        self.add(CmdHome)
        self.add(CmdPage)
        self.add(CmdPose)
        self.add(CmdZone)
        self.add(CmdSpoof)
        self.add(CmdPortal)
        self.add(CmdWhisper)
        self.add(CmdInventory)
# [...] # Clothing contrib commands:
        self.add(CmdWear)
        self.add(CmdRemove)
        self.add(CmdCover)
        self.add(CmdUncover)
# [...] Travel related commands:
        self.add(CmdStop)
        self.add(CmdBack)
        self.add(CmdSpeed)
        self.add(CmdContinue)


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    key = 'DefaultAccount'

    def at_cmdset_creation(self):
        """Populates the DefaultAccount cmdset"""
        super(AccountCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdCWho)
        self.remove(default_cmds.CmdCBoot)
        self.remove(default_cmds.CmdPage)
        self.remove(default_cmds.CmdQuit)
        self.remove(default_cmds.CmdCdesc)
        self.remove(default_cmds.CmdClock)
        self.remove(default_cmds.CmdCemit)
        self.remove(default_cmds.CmdAddCom)
        self.remove(default_cmds.CmdDelCom)
        self.remove(default_cmds.CmdAllCom)
        self.remove(default_cmds.CmdCdestroy)
        self.remove(default_cmds.CmdChannels)
        self.remove(default_cmds.CmdChannelCreate)
# [...]
        self.add(CmdSay)
        self.add(CmdTry)
        self.add(CmdWho)
        self.add(CmdMail)
        self.add(CmdPage)
        self.add(CmdPose)
        self.add(CmdQuit)
        self.add(CmdTime)
        self.add(CmdAbout)
        self.add(CmdAudit)
        self.add(CmdSense)
        self.add(CmdAccess)
        self.add(CmdChange)
        self.add(CmdChannels)
        self.add(building.CmdTeleport)
# [...] Account commands:
        self.add(CmdIC)
        self.add(CmdOOC)
        self.add(CmdQuell(locks='cmd:perm(denizen)'))
        self.add(CmdOption)
        self.add(CmdPassword(locks='cmd:perm(denizen)'))
        self.add(CmdSessions)
        self.add(CmdColorTest)
        # self.add(CmdChannelWizard) # TODO: Still under development.


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """
    key = 'DefaultUnloggedin'

    def at_cmdset_creation(self):
        """Populates the DefaultUnloggedin cmdset"""
        super(UnloggedinCmdSet, self).at_cmdset_creation()
        self.add(prelogin.CmdWhoUs())
        self.add(prelogin.CmdUnconnectedEncoding())
        self.add(prelogin.CmdUnconnectedConnect())
        self.add(prelogin.CmdUnconnectedCreate())
        self.add(prelogin.CmdUnconnectedQuit())
        self.add(prelogin.CmdUnconnectedLook())
        self.add(prelogin.CmdUnconnectedAbout())
        self.add(prelogin.CmdUnconnectedHelp())
        self.add(prelogin.CmdUnconnectedScreenreader())


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in.
    It is empty by default.
    """
    key = 'DefaultSession'

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super(SessionCmdSet, self).at_cmdset_creation()
        self.add(CmdMenu)
        self.add(CmdRoll)
