# -*- coding: utf-8 -*-
from commands.command import MuxCommand  # Used in CmdWall


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
    locks = 'cmd:perm(wall) or perm(wizard)'
    help_category = 'Administration'

    def func(self):
        """Implements command"""
        if not self.args:
            self.caller.msg('Usage: {} <message>'.format(self.cmdstring))
            return
        message = '### %s%s|n shouts "|w%s|n"' % (self.caller.STYLE, self.caller.name, self.args)
        self.msg("Announcing to all connections ...")
        SESSIONS.announce_all(message)
