# -*- coding: utf-8 -*-
from commands.command import MuxCommand
from evennia.utils import utils
import time  # Check time since last visit
import os
import sys
import twisted
import django


class CmdAbout(MuxCommand):
    """
    Display info about NOW or target.
    Usage:
      about [target]
    """
    key = 'about'
    aliases = ['last', 'finger', 'pinfo', 'cinfo', 'info']
    help_category = 'Information'
    locks = 'cmd:all()'
    account_caller = True

    def func(self):
        """Display information about server or target"""
        sessions = self.account.sessions.get()
        session = sessions[-1] if sessions else None
        account = self.account
        char = self.character or account.db._last_puppet
        if not char:
            if account.db._playable_characters[0]:
                char = account.db._playable_characters[0]
            else:
                self.msg('You must have a character to interact with objects.')
                return
        cmd = self.cmdstring
        opt = self.switches
#        args = unicode(self.args).strip()
        args = self.args.strip()
        message = ''
        if args:
            obj = char.search(args, global_search=True)

            if obj:
                display_name = obj.get_display_name(char)
                object_summary = ''
                if obj.db.desc_brief or obj.db.messages and obj.db.messages.get('summary'):
                    object_summary = '|w' + (obj.db.desc_brief or obj.db.messages
                                             and obj.db.messages.get('summary', ''))
                object_name = (display_name + ' is |w' + repr(obj) + ' ' + object_summary +
                               (('|wAliases: |C' + '|w, |C'.join(str(obj.aliases).split(',')))
                               if str(obj.aliases) else '') +
                               ' |gcreated on |g' + str(obj.db_date_created)[:10])
                last_on = 0
                on_count = 0
                if obj.db.puppeted:
                    times_awake = []
                    times_asleep = []
                    for each in obj.db.puppeted.values():
                        times_awake.append(each[0])
                        times_asleep.append(each[1])
                        on_count += each[2]
                    time_awake = max(times_awake) if times_awake else None
                    time_asleep = max(times_asleep) if times_asleep else None
                    last_on_value = abs(time_awake - time_asleep) if (time_awake and time_asleep) else 0
                    last_on = utils.time_format(last_on_value, 2) if last_on_value else 'None'
                    if time_asleep:
                        last_asleep = utils.time_format(int(time.time()) - time_asleep, 2) + ' ago'
                    else:
                        last_asleep = 'and is awake now' if obj.has_account else 'unknown'
                else:
                    last_awake, last_asleep = 'unknown', 'unknown'
                if obj.has_account:  # Object is awake:
                    message = '{} is currently awake.'.format(obj.get_display_name(char))
                elif obj.db.puppeted:
                    message = '{} was last awake {} for {}.'.format(
                        obj.get_display_name(char), last_asleep, last_on)
                else:
                    message = '{} has no known last awake time.'.format(obj.get_display_name(char))
                if 'last' in opt or 'last' in cmd:
                    char.msg(message)
                    return
                # If object has never been puppeted, use a different template that
                # does not include Awake count, awake times, and CPU use.
                from evennia import EvForm, EvTable
                if obj.db.puppeted:
                    time_summary = (message +
                                    ' Awake ' + str(on_count) + ' time' + ('' if on_count == 1 else 's') +
                                    '. CPU use: ' + str(round(obj.traits.ct.current, 4)) + ' seconds, ' +
                                    str(obj.traits.cc.current) + ' commands, average ' +
                                    str(round(obj.traits.ct.current / obj.traits.cc.current, 4)) + ' sec each.')
                    form_file = 'awakeformunicode' if session.protocol_flags['ENCODING'] == 'utf-8' else 'awakeform'
                    form = EvForm('commands/forms/{}.py'.format(form_file))
                    form.map(cells={1: object_name,
                                    2: time_summary,
                                    3: obj.db.messages and obj.db.messages.get('species', ''),
                                    4: obj.db.messages and obj.db.messages.get('gender', ''),
                                    5: obj.db.desc})
                else:
                    form_file = 'objectformunicode' if session.protocol_flags['ENCODING'] == 'utf-8' else 'objectform'
                    form = EvForm('commands/forms/{}.py'.format(form_file))
                    form.map(cells={1: object_name,
                                    2: obj.db.messages and obj.db.messages.get('species', ''),
                                    3: obj.db.messages and obj.db.messages.get('gender', ''),
                                    4: obj.db.desc})
#                message = unicode(form)
                message = str(form)
        else:
            if 'last' in opt or 'last' in cmd:
                message = 'Usage: last <character name>'
            else:
                message = """
                |cEvennia|n %s|n
                MUD/MUX/MU* development system
                |wLicense|n https://opensource.org/licenses/BSD-3-Clause
                |wWeb|n http://evennia.com
                |wIrc|n #evennia on FreeNode
                |wForum|n http://evennia.com/discussions
                |wMaintainer|n (2010-)   Griatch (griatch AT gmail DOT com)
                |wMaintainer|n (2006-10) Greg Taylor
                |wOS|n %s
                |wPython|n %s
                |wTwisted|n %s
                |wDjango|n %s
                """ % (utils.get_evennia_version(),
                       os.name,
                       sys.version.split()[0],
                       twisted.version.short(),
                       django.get_version())
        # char.msg(image=['https://raw.githubusercontent.com/evennia/evennia/'
        #                 'master/evennia/web/website/static/website/images/evennia_logo.png'])
        self.msg((message, {"type": "help"}))
        # char.private(None, 'info', message)
