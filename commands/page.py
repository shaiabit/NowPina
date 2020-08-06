# -*- coding: utf-8 -*-
from commands.command import MuxCommand


class CmdPage(MuxCommand):
    """
    Command to forward pages into publc channel.
    """
    key = 'page'
    aliases = ['p']
    locks = 'cmd:all()'
    arg_regex = r'\s|$'

    def func(self):
        """Process the command"""
        self.account.execute_cmd('public {}'.format(self.args))
