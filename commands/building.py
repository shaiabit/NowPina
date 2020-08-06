# -*- coding: utf-8 -*-
"""
Building and world design commands
from evennia/commands/default/building.py
Allows for customizations by importing them here.
"""
from builtins import range

import re
from django.conf import settings
from django.db.models import Q
from evennia.objects.models import ObjectDB
from evennia.locks.lockhandler import LockException
from evennia.commands.cmdhandler import get_and_merge_cmdsets
from evennia.utils import create, utils, search
from evennia.utils.utils import inherits_from, class_from_module
from evennia.utils.eveditor import EvEditor
#from evennia.utils.spawner import spawn
from evennia.utils.ansi import raw

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

# limit symbol import for API
__all__ = ("ObjManipCommand", "CmdSetObjAlias", "CmdCopy",
           "CmdCpAttr", "CmdMvAttr", "CmdCreate",
           "CmdDesc", "CmdDestroy", "CmdDig", "CmdTunnel", "CmdLink",
           "CmdUnLink", "CmdSetHome", "CmdListCmdSets", "CmdName",
           "CmdOpen", "CmdSetAttribute", "CmdTypeclass", "CmdWipe",
           "CmdLock", "CmdExamine", "CmdFind", "CmdTeleport",
           "CmdScript", "CmdTag", "CmdSpawn")

try:
    # used by @set
    from ast import literal_eval as _LITERAL_EVAL
except ImportError:
    # literal_eval is not available before Python 2.6
    _LITERAL_EVAL = None

# used by @find
CHAR_TYPECLASS = settings.BASE_CHARACTER_TYPECLASS
ROOM_TYPECLASS = settings.BASE_ROOM_TYPECLASS
EXIT_TYPECLASS = settings.BASE_EXIT_TYPECLASS
_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH

_PROTOTYPE_PARENTS = None

from evennia.commands.default.building import ObjManipCommand
from evennia.commands.default.building import CmdSetObjAlias
from evennia.commands.default.building import CmdCopy
from evennia.commands.default.building import CmdCpAttr
from evennia.commands.default.building import CmdMvAttr
from evennia.commands.default.building import CmdCreate

from evennia.commands.default.building import _desc_load
from evennia.commands.default.building import _desc_save
from evennia.commands.default.building import _desc_quit

from evennia.commands.default.building import CmdDig
from evennia.commands.default.building import CmdTunnel
from evennia.commands.default.building import CmdLink
from evennia.commands.default.building import CmdUnLink
from evennia.commands.default.building import CmdSetHome
from evennia.commands.default.building import CmdListCmdSets
from evennia.commands.default.building import CmdName
from evennia.commands.default.building import CmdOpen
from evennia.commands.default.building import _convert_from_string
from evennia.commands.default.building import CmdSetAttribute
from evennia.commands.default.building import CmdTypeclass
from evennia.commands.default.building import CmdWipe
from evennia.commands.default.building import CmdLock
from evennia.commands.default.building import CmdExamine
from evennia.commands.default.building import CmdFind
from commands.command import MuxCommand  # Used in CmdTeleport
from evennia.commands.default.building import CmdScript
from evennia.commands.default.building import CmdTag
from evennia.commands.default.building import CmdSpawn


class CmdTeleport(MuxCommand):
    """
    Change object's location - IC component-aware.
    if target has a location, the teleport will be to its location by default.
    If no object is given, you are teleported.

    Usage:
      tel[/option] [<object> =|to] <target's location>
    Options:
    /quiet     don't echo leave/arrive messages to the source/target
               locations for the move.
    /into      if target is an exit, teleport INTO the object
               instead of to its location or destination.
    /vanish    if set, teleport the object into Nothingness. If this
               option is used, <target location> is ignored.
               Note that the only way to retrieve an object from
               Nothingness is by direct #dbref reference.
    Examples:
      tel Limbo
      tel Rulan to me
      tel/quiet box=fog
      tel/into book to shelf
      tel/vanish box
    """
    key = 'teleport'
    aliases = ['tport', 'tel']
    options = ('quiet', 'silent', 'into', 'vanish')
    locks = 'cmd:perm(teleport) or perm(builder)'
    help_category = 'Travel'
    parse_using = ' to '

    @staticmethod
    def stop_check(target):
        """
        Forbidden items do not teleport.

        Marked by tags, they are either left behind (teleport:remain),
         or they prevent their holder to teleport (teleport:forbid).

        """

        def tag_check(obj):
            if obj.tags.get('teleport', category='forbid'):
                return False
            if obj.tags.get('teleport', category='remain'):
                return None
            return True

        # Test target and target's contents:
        items, result = [target] + target.contents, []
        for each in items:
            check = tag_check(each)
            if not check:
                result.append((each, check))
        return True if not result else result

    @staticmethod
    def special_name(text, who):
        text = text.lower()
        if text == 'home':
            return who.home
        elif text in ('homeroom', 'home room', 'room'):
            return who.db.objects['home'] if (who.db.objects and who.db.objects.get('home', False)) else who.home
        elif text in ('me', 'self'):
            return who

    def func(self):
        """Performs the teleport, accounting for in-world conditions."""

        char = self.character
        cmd = self.cmdstring
        account = self.account
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        if lhs.startswith('to ') and not rhs:  # Additional parse step when left of "to" is left empty.
            lhs, rhs = 'me', lhs[3:].strip()
        opt = self.switches

        if char and char.ndb.currently_moving:
            account.msg("You can not teleport while moving. (|rstop|n, then try again.)")
            return

        # setting command options
        tel_quietly = 'quiet' in opt or 'silent' in opt
        to_none = 'vanish' in opt

        search_as = account.db._playable_characters[0]
        if not search_as:
            search_as = account.db._last_puppet
        if not search_as:
            account.msg("|yMust be |c@ic|y to use |g%s|w." % cmd)
            return

        if to_none:  # teleporting to Nothingness
            if not args and char:
                target = char
                account.msg('Teleported to ' + settings.NOTHINGNESS + '|n.')
                if char and char.location and not tel_quietly:
                    char.location.msg_contents("|r%s|n vanishes." % char, exclude=char)
            else:
                if args == 'home':
                    target = char.home
                else:
                    target = search_as.search(lhs, global_search=True, exact=False)
                if not target:
                    account.msg('Did not find object to teleport.')
                    return
                if not (account.check_permstring('mage') or target.access(account, 'control')):
                    account.msg('You must have |wMage|n or higher power to '
                                'send something into ' + settings.NOTHINGNESS + '|n.')
                    return
                account.msg('Teleported %s -> None-location.' % (target.get_display_name(char)))
                if target.location and not tel_quietly:
                    if char and char.location == target.location and char != target:
                        target.location.msg_contents('%s%s|n sends %s%s|n into ' %
                                                     (char.STYLE, char, target.STYLE, target)
                                                     + settings.NOTHINGNESS + '|n.')
                    else:
                        target.location.msg_contents('|r%s|n vanishes into' % target + settings.NOTHINGNESS + '|n.')
            target.location = None
            return
        if not args:
            account.msg("Usage: teleport[/options] [<obj> =|to] <target>")
            return
        if rhs:
            right_result = self.special_name(rhs, char)
            left_result = self.special_name(lhs, char)
            target = search_as.search(lhs, global_search=True, exact=False) if not left_result else left_result
            loc = search_as.search(rhs, global_search=True, exact=False) if not right_result else right_result
        else:
            target = char
            left_result = self.special_name(lhs, target)
            loc = search_as.search(lhs, global_search=True, exact=False) if not left_result else left_result
        if not target:
            account.msg("Did not find object to teleport.")
            return
        if not loc:
            account.msg("Destination not found.")
            return
        be_with = loc
        use_loc = True
        if 'into' in opt:
            use_loc = False
        elif loc.location:
            loc = loc.location
        if target == loc:
            account.msg("You can not teleport an object inside of itself!")
            return
        if target == loc.location:
            account.msg("You can not teleport an object inside something it holds!")
            return
        if target.location and target.location == loc:
            with_clause = ' with %s' % be_with.get_display_name(char) if be_with is not loc else ''
            account.msg("%s is already at %s%s." % (target.get_display_name(char),
                                                    loc.get_display_name(char), with_clause))
            return
        print("%s is about to go to %s" % (target.key, loc.key))
        scan = self.stop_check(target)
        if scan is not True:
            print("Teleport contraband detected: " + ', '.join([repr(each) for each in scan]))
        if target == char:
            account.msg('Personal teleporting costs 1 coin.')
            target.nattributes.remove('exit_used')  # Remove reference to using exit when not using exit to leave
        else:
            target.ndb.mover = char or account
        if target.move_to(loc, quiet=tel_quietly, emit_to_obj=char, use_destination=use_loc):
            if char and target == char:
                account.msg("Teleported to %s." % loc.get_display_name(char))
            else:
                account.msg("Teleported %s to %s." % (target.get_display_name(char), loc.get_display_name(char)))
                target.nattributes.remove('mover')
            if target.location and target.db.prelogout_location and not target.has_account:
                target.db.prelogout_location = target.location  # Have Character awaken here.
        else:
            if target.location != loc:
                account.msg("|rFailed to teleport %s to %s." % (target.get_display_name(char),
                                                                loc.get_display_name(char)))


# To use the prototypes with the @spawn function set
#   PROTOTYPE_MODULES = ["commands.prototypes"]
# Reload the server and the prototypes should be available.

