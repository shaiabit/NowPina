# -*- coding: utf-8 -*-
from django.conf import settings
from commands.command import MuxCommand


class CmdAccess(MuxCommand):
    """
    Usage:
      access      -  Display your account and character access level.
      hierarchy   -  Displays the system's permission groups hierarchy.
      levels      -  Alias for hierarchy.
    """
    key = 'access'
    aliases = ['hierarchy', 'levels']
    locks = 'cmd:all()'
    help_category = 'Information'
    account_caller = True

    def func(self):
        """Load the permission groups"""
        char = self.character
        account = self.account
        hierarchy_full = settings.PERMISSION_HIERARCHY
        info = []  # List of info to output to user
        if 'hierarchy' in self.cmdstring or 'levels' in self.cmdstring:
            info.append('|wPermission Hierarchy|n (climbing): %s|/' % ", ".join(hierarchy_full))
        else:
            pperms = ', '.join(account.permissions.all())
            cperms = (', '.join(char.permissions.all())) if char else None
            if account.is_superuser:
                pperms = '<|ySuperuser|n> ' + pperms
                cperms = ('<|ySuperuser|n> ' + cperms) if cperms else None
            info.append('|wYour Account' + ('/Character' if char else '') + ' access|n: ')
            if account:
                if account.attributes.has('_quell'):
                    info.append('|r(quelled)|n ')
                info.append('Account: (%s: %s)' % (account.get_display_name(account), pperms))
            if cperms:
                info.append(' and Character (%s: %s)' % (char.get_display_name(char), cperms))
        self.msg(''.join(info))
