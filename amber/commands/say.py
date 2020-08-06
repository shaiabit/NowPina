# -*- coding: utf-8 -*-
import re
from commands.command import MuxCommand
from evennia.utils import ansi
from evennia.utils.utils import pad, justify
from world.helpers import escape_braces, substitute_objects


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say[/option] <message>
    Options:
    /ooc  - Out-of-character to the room.
    /verb - set default say verb.
    """
    key = 'say'
    aliases = ['"', "'"]
    switch_options = ('ooc', 'quote', 'verb')
    arg_regex = None
    locks = 'cmd:all()'

    def func(self):
        """Run the say command"""
        sess = self.session
        account = self.account
        char = self.character
        here = char.location if char else None
        opt = self.switches
        args = self.args.strip()
        if not (here and char):
            if args:
                account.execute_cmd('pub %s' % args, session=ses)
            else:
                self.msg('Usage: say <message>   to speak on public channel.')
            return
        if not args:
            account.execute_cmd("help say", session=sess)
            return
        if 'verb' in opt:
            char.attributes.add('say-verb', args)
            here.msg_contents(text=('{char} warms up vocally with "%s|n"' % escape_braces(args),
                                    {'type': 'pose', 'action': True}),
                              from_obj=char, mapping=dict(char=char))
            return
        if 'quote' in opt:
            if len(args) > 2:
                char.quote = args  # Not yet implemented.
                return
        else:
            speech = substitute_objects(args, char)
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            say_prepend = char.db.messages and char.db.messages.get('say prepend')
            prepend = say_prepend if say_prepend else '|w'
            if 'ooc' in opt:
                here.msg_contents(text=('[OOC] {char} says, |n"|w%s|n"' % escape_braces(speech),
                                        {'type': 'say', 'ooc': True}), from_obj=char, mapping=dict(char=char))
                if here.has_account:
                    here.msg(text=('[OOC] %s says, |n"|w%s|n"' % (char.get_display_name(here), escape_braces(speech)),
                                   {'type': 'say', 'ooc': True}), from_obj=char)
            else:
                here.msg_contents(text=('{char} %s, |n"%s%s|n"' % (escape_braces(verb), escape_braces(prepend),
                                                                   escape_braces(speech)),
                                        {'type': 'say'}), from_obj=char, mapping=dict(char=char))
                if here.has_account:
                    here.msg(text=('From inside you, %s %s, |n"%s%s|n"' %
                                   (char.get_display_name(here), escape_braces(verb), escape_braces(prepend),
                                    escape_braces(speech)), {'type': 'say'}), from_obj=char)


class CmdOoc(MuxCommand):
    """
    Send an out-of-character message to your current location.
    Usage:
      ooc <message>
      ooc :<message>
      ooc "<message>.
    """
    key = 'ooc'
    aliases = ['_']
    arg_regex = None
    locks = 'cmd:all()'

    def func(self):
        """Run the ooc command"""
        sess = self.session
        account = self.account
        char = self.character
        here = char.location
        args = self.args.strip()
        if not args:
            account.execute_cmd('help ooc', session=sess)
            return
        elif args[0] == '"' or args[0] == "'":
            account.execute_cmd('say/o ' + args[1:], session=sess)
        elif args[0] == ':' or args[0] == ';':
            account.execute_cmd('pose/o %s' % args[1:], session=sess)
        else:
            here.msg_contents(text=('[OOC {char}] %s' % escape_braces(args), {'type': 'ooc', 'ooc': True}),
                              from_obj=char, mapping=dict(char=char))
            if here.has_account:
                here.msg(text=('[OOC %s] %s' %
                               (char.get_display_name(here), escape_braces(args)),
                               {'type': 'ooc', 'ooc': True}), from_obj=char)


class CmdSpoof(MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>   or
      .<literal text>
    Switches:
    /center <msg> [ = position ]  Center msg at position
    /right <msg> [ = position ]   Align right at position
    /indent <msg> [ = position ]  Begin msg starting at position
    /news <message> [ = <width> [indent] ]
    /strip <message sent to room with markup stripped>
    /self <message only to you with full markup>
    """
    key = 'spoof'
    aliases = ['.', 'sp']
    switch_options = ('center', 'right', 'indent', 'news', 'strip', 'self')
    arg_regex = None
    locks = 'cmd:all()'

    def func(self):
        """Run the spoof command"""
        char = self.character
        cmd = self.cmdstring
        here = char.location
        opt = self.switches
        args = self.args
        to_self = 'self' in opt or not here
        if not args:
            self.account.execute_cmd('help spoof', session=self.session)
            return
        # Optionally strip any markup /or/ just escape it,
        stripped = ansi.strip_ansi(args)
        spoof = stripped if 'strip' in opt else args.replace('|', '||')
        if 'indent' in opt:
            indent = 20
            if self.rhs:
                args = self.lhs.strip()
                indent = re.sub("[^0123456789]", '', self.rhs) or 20
                indent = int(indent)
            if to_self:
                char.msg(' ' * indent + args.rstrip())
            else:
                here.msg_contents(text=(' ' * indent + escape_braces(args.rstrip()), {'type': 'spoof'}))
        elif 'right' in opt or 'center' in opt or 'news' in opt:  # Use Justify
            if self.rhs is not None:  # Equals sign exists.
                parameters = '' if not self.rhs else self.rhs.split()
                args = self.lhs.strip()
                if len(parameters) > 1:
                    if len(parameters) == 2:
                        outside, inside = self.rhs.split()
                    else:
                        outside, inside = [parameters[0], parameters[1]]
                    outside = re.sub("[^0123456789]", '', outside) or 0
                    inside = re.sub("[^0123456789]", '', inside) or 0
                    outside, inside = [int(max(outside, inside)), int(min(outside, inside))]
                else:
                    outside, inside = [72, 20]
            else:
                outside, inside = [72, min(int(self.rhs or 72), 20)]
            block = 'l'
            if 'right' in opt:
                block = 'r'
            elif 'center' in opt:
                block = 'c'
            elif 'news' in opt:
                block = 'f'
            for text in justify(args, width=outside, align=block, indent=inside).split('\n'):
                if to_self:
                    char.msg(text.rstrip())
                else:
                    here.msg_contents(text=(escape_braces(text.rstrip()), {'type': 'spoof'}))
        else:
            if 'strip' in opt:  # Optionally strip any markup or escape it,
                if to_self:
                    char.msg(spoof.rstrip(), options={'raw': True})
                else:
                    here.msg_contents(text=(escape_braces(spoof.rstrip()), {'type': 'spoof'}), options={'raw': True})
            elif '.' in cmd:  # Leave leading spacing intact by using self.raw and not stripping left whitespace
                # Adding <pre> and </pre> to all output in case one of the viewers is using webclient
                spoof = self.raw.rstrip()
                if to_self:
                    char.msg(('<code>' + spoof + '</code>', {'type': 'spoof'}), options={'raw': True})
                else:
                    here.msg_contents(text=('<code>' + spoof + '</code>', {'type': 'spoof'}), options={'raw': True})
            else:
                if to_self:
                    char.msg(args.rstrip())
                else:
                    here.msg_contents(text=(escape_braces(spoof.rstrip()), {'type': 'spoof'}))
