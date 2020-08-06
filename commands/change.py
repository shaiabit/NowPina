# -*- coding: utf-8 -*-
from commands.command import MuxCommand


class CmdChange(MuxCommand):
    """
    Operate various aspects of character configuration.
    Usage:
      change[/option] [setting] [=|to value]
    Options:
    /on     Change a setting to 'on'
    /off    Change a setting to 'off'
    /value  Change a setting to a numeric value
    /symbol Change a setting to a single character
    /clear  Cause a setting to be removed
    /show   Display the value of settings starting with
    /verb   Change or display the key of a verb
    /detail Set the text for this object's detail entry
    /sense  Link a sense to a detail entry

    Not supplying a setting assumes you just want to view all settings.
    Not supplying a value assumes you just want to toggle the value on/off.
    """
    key = 'change'
    aliases = ['clear', 'show']
    locks = 'cmd:all()'
    options = ('on', 'off', 'value', 'symbol', 'clear', 'show', 'verb', 'detail', 'sense')
    parse_using = ' to '
    help_category = 'Building'
    account_caller = True

    def func(self):
        """
        This function tries to be user-friendly, and allow
        any messages and settings to be configured on the
        character or the current room the character is in
        and can edit.  Name-changing functionality coming soon.
        """
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        char = self.character
        # where = self.obj
        account = self.account
        setting = char.db.settings or {}
        message = char.db.messages or {}

        if lhs == 'desc':
            extra = (' ' + rhs) if rhs else ''
            char.execute_cmd('desc' + extra)
            return
        if lhs == 'name':
            extra = (' ' + rhs) if rhs else ''
            char.execute_cmd('name' + extra)
            return
        if ' to ' in lhs or '=' in lhs:
            self.msg('Invalid key string:  Key can not contain = or " to ".   Nothing done.')
            return

        if 'clear' in cmd or 'clear' in opt:
            # The key on the left is removed from storage.  All settings and messages
            # are arbitrary, and no setting is mandatory, so removal of any setting
            # by the user has no critical consequence.
            # CHANGE/clear <key>   removes a bool
            if not rhs:
                if rhs is None:
                    # CHANGE/clear <key> <=| to>   removes a message
                    was = (lhs in char.db.settings and char.db.settings.pop(lhs)) or None
                    self.msg('Setting {} ({}) removed.'.format(lhs, was))
                else:
                    # TODO: clear command/option functionality for value and symbol
                    # CHANGE/clear/value <key> <=| to>   removes a value
                    if 'value' in opt:
                        self.msg('Functionality not complete. Nothing done.')
                    # CHANGE/clear/symbol <key> <=| to>   removes a symbol
                    elif 'symbol' in opt:
                        self.msg('Functionality not complete. Nothing done.')
                    else:
                        was = (lhs in char.db.messages and char.db.messages.pop(lhs)) or None
                        self.msg('Message {} ({}) removed.'.format(lhs, was))
            else:
                self.msg('Functionality not complete. Nothing done.')
            return

        if 'name' in opt:  # TODO: name command/option functionality
            # The name of the object on the left is renamed with the new name on the right.
            self.msg('Name of {0} changed to {1}.'.format(lhs, rhs))
            # For this to work, the left side must be matched with a local object.
            # The local object matching must be controlled by the user,
            # otherwise access to change the object's name is denied.
            self.msg('Functionality not complete. Nothing done.')
            return

        if 'verb' in opt:  # TODO: verb command/option functionality
            # The name of the verb on the left is keyed with the lock string on the right.
            self.msg('Verb {0} key set to {1}.'.format(lhs, rhs))
            # For this to work, a deeper information structure of verbs must exist.
            self.msg('Functionality not complete. Nothing done.')
            return

        if 'detail' in opt:  # TODO: detail command/option functionality
            # The name of the verb on the left is keyed with the lock string on the right.
            self.msg('Detail {0} key set to {1}.'.format(lhs, rhs))
            # The name of the detail is an aspect of the object,
            # accessible by sensing the possessive form:
            #   <sense> <object>'s <detail>
            # omit <object>'s if object is the location (here).
            self.msg('Functionality not complete. Nothing done.')
            return

        if 'sense' in opt:  # TODO: sense command/option functionality
            # The name of the verb on the left is keyed with the lock string on the right.
            self.msg('Sense {0} key set to {1}.'.format(lhs, rhs))
            # For this to work, a detail key of the sense's value should already exist.
            self.msg('Functionality not complete. Nothing done.')
            return

        if not args or 'show' in cmd or 'show' in opt:
            messages = char.db.messages
            if not messages:
                char.db.messages = {}
            messages_filtered = {i: messages[i] for i in messages if i.lower().startswith(args.lower())} if\
                args else messages
            if messages_filtered:
                account.msg('Listing %s message settings: |g%s' % (
                    char.get_display_name(account), '|n, |g'.join('|g%s|n: |c%s|n' % (each, messages_filtered[each])
                                                                  for each in messages_filtered)))
            else:
                account.msg('No messages to change yet.')
            settings = char.db.settings
            if not settings:
                char.db.settings = {}
            settings_filtered = {i: settings[i] for i in settings if i.lower().startswith(args.lower())} if\
                args else settings
            if settings_filtered:
                account.msg('Listing %s control panel settings: |g%s' % (
                    char.get_display_name(account), '|n, |g'.join('|lcchange %s|lt%s|le|n: |c%s' % (
                        each, each, settings_filtered[each]) for each in settings_filtered)))
            else:
                account.msg('No toggle settings to change yet.')
            return  # Listing messages and settings is done
        # Some other action still needs to be done
        action = 'message' if rhs else 'toggle'
        if (rhs and rhs.lower() in ('on', 'true', '1', 'yes')) or opt and opt[0] == 'on':
            action = 'on'
        elif (rhs and rhs.lower() in ('off', 'false', '0', 'no')) or opt and opt[0] == 'off':
            action = 'off'
        #  Action is acted upon depending on what is needed to be done
        if action == 'on':
            action = 'engage'
            setting[args] = True
            status = True
        elif action == 'off':
            action = 'disengage'
            setting[args] = False
            status = False
        elif action == 'value':
            action = 'dial'
            setting[lhs] = int(rhs)
            status = int(rhs)
        elif action == 'symbol':
            action = 'dial'
            setting[lhs] = rhs
            status = rhs
        elif action == 'message':
            action = 'set'
            message[lhs] = rhs
            status = rhs
        else:  # Toggle setting
            setting[args] = False if char.db.settings and args in char.db.settings\
                                     and char.db.settings[args] else True
            status = setting[args]
        if rhs:
            string = '|wYou %s "%s" to "%s" on %s.' % \
                      (action, lhs.replace('|', '||') if lhs else 'something', rhs.replace('|', '||'),
                       char.get_display_name(account))
        else:
            string = '|wYou %s "%s" on %s to "%s".' %\
                      (action, args.replace('|', '||') if args else 'something', char.get_display_name(account), status)

        special_message = {
             'broadcast commands/True': "|wYou broadcast commmands now.",
             'broadcast commands/False': "|wYou don't broadcast commands now.",
             'see commands/True': "|wYou see broadcasted commands now.",
             'see commands/False': "|wYou don't see broadcasted commands now.",
             'look arrive/True': "|wYou look when you arrive in a new location.",
             'look arrive/False': "|wYou don't look when you arrive in a new location.",
             'look notify/True': "|wYou are notified when someone looks at you.",
             'look notify/False': "|wYou are not notified when someone looks at you.",
             'carry others/True': "|wTou allow others to follow you.",
             'carry others/False': "|wYou don't allow others to follow you."
            }

        account.msg(special_message.get(f'{args}/{status}', string))

        if action == 'set' and rhs:
            char.db.messages = message
        else:
            char.db.settings = setting
