# -*- coding: utf-8 -*-
"""
The commands for helpstaff level are gathered here.
Helpstaff is the lowest level of staff, and one step higher than builder,
so typically requires knowledge of building commands to be effective.
"""
from commands.command import MuxCommand
from django.conf import settings
from evennia import utils
from evennia.server.sessionhandler import SESSIONS  # Used for CmdWall

# error return function, needed for search
_AT_SEARCH_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit('.', 1))


class CmdAudit(MuxCommand):
    """
    Audit to show hosting activity
    Usage:
      audit [tangible]
    """
    key = '@audit'
    locks = 'cmd:perm(audit) or perm(helpstaff)'
    help_category = 'Helpstaff'
    account_caller = True

    def func(self):
        """Implements viewing visitor log for this object."""
        char = self.character
        # cmd = self.cmdstring
        loc = char.location
        # account = self.account
        args = self.args
        # lhs, rhs = self.lhs, self.rhs
        # opt = self.switches
        obj_list = char.search(args, quiet=True, candidates=[loc] + loc.contents + char.contents) if args else [char]
        if not obj_list:
            _AT_SEARCH_RESULT(obj_list, char, args, quiet=False)
            return  # Trying to audit something that isn't there. "Could not find ''."
        obj = obj_list[0]
        obj_name = obj.get_display_name(char)
        hosted = obj.db.hosted
        if hosted:
            import time
            from evennia.utils import utils, evtable
            now = int(time.time())
            table = evtable.EvTable(border='none', pad_width=0, border_width=0, maxwidth=79)
            table.add_header(obj_name, '|wTimes', '|cLast', '|gFrom')
            table.reformat_column(0, width=25, align='l')
            table.reformat_column(1, width=7, align='c')
            table.reformat_column(2, width=35, align='l')
            table.reformat_column(3, width=25, pad_right=1, align='l')
            for each in hosted:
                delta_t = now - hosted[each][0]
                v_name = each.get_display_name(char)
                v_count = hosted[each][2]
                from_name = hosted[each][1].get_display_name(char) if hosted[each][1] else '|where|n'
                table.add_row(v_name, v_count, utils.time_format(delta_t, 2), from_name)
            self.msg('[begin] Audit showing visits to:')
            self.msg(table)
            self.msg('[end] Audit of {}'.format(obj_name))
        else:
            self.msg('No audit information for {}.'.format(obj_name))


class CmdWall(MuxCommand):
    """
    make an announcement to all

    Usage:
      @wall <message>

    Announces a message to all connected sessions
    including all currently unlogged in.
    """
    key = '@wall'
    aliases = ['announce']
    locks = 'cmd:perm(wall) or perm(helpstaff)'
    help_category = 'Administration'

    def func(self):
        """Implements command"""
        if not self.args:
            self.caller.msg('Usage: {} <message>'.format(self.cmdstring))
            return
        message = '### %s%s|n shouts "|w%s|n"' % (self.caller.STYLE, self.caller.name, self.args)
        self.msg("Announcing to all connections ...")
        SESSIONS.announce_all(message)
