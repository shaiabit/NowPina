# -*- coding: utf-8 -*-
import time
from commands.command import MuxAccountCommand
from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import ansi, utils, create, search, evtable


class CmdWho(MuxAccountCommand):
    """
    Shows who is currently online
    with optional sorting and
    starts-with filter.
    Usage:
      who[/option] [filter]   - basic view
      where[/option] [filter] - includes location
      what[/option] [filter]  - includes doing
      ws[/option] [filter]    - includes species
      wa[/option] [filter]    - same as 'where'
    Options:
    /alpha   - sort table alphabetically
    /on      - sort table by online time
    /idle    - sort table by idle time
    /reverse - sort in reverse order
    /exact   - Only match exact when filtering
    """
    key = 'who'
    aliases = ['ws', 'where', 'wa', 'what', 'wot']
    options = ('alpha', 'on', 'idle', 'reverse', 'exact')
    arg_regex = None
    locks = 'cmd:all()'

    def func(self):
        """Get all connected accounts by polling session."""
        you = self.account
        opt = self.switches
        args = self.args
        session_list = SESSIONS.get_sessions()
        notice = ''
        if args:
            char = self.caller.get_puppet(self.session)
            if 'exact' in opt:
                session_list = [sess for sess in session_list if sess.get_puppet()
                                and sess.get_puppet().get_display_name(char, plain=True) == args]
                notice = '  Showing exact matches for "{}"'.format(args)
            else:
                args = args.lower()
                session_list = [sess for sess in session_list if sess.get_puppet()
                                and sess.get_puppet().get_display_name(char, plain=True).lower().startswith(args)]
                notice = '  Showing matches that begin with "{}"'.format(args)
        sessions_using_puppets = [sess for sess in session_list if sess.get_puppet()]
        cmd = self.cmdstring
        show_session_data = you.check_permstring('immortal') and not you.attributes.has('_quell')
        table = evtable.EvTable(border='none', pad_width=0, border_width=0, maxwidth=79)
        if cmd == 'wa' or cmd == 'where':
            # Example output expected:
            # Occ, Location,  Avg Time, Top 3 Active, Directions
            # #3        Park            5m              Rulan, Amber, Tria              Taxi, Park
            # Other possible sort methods: Alphabetical by name, by occupant count, by activity, by distance
            # Nick = Global Nick (no greater than five A/N or randomly created if not a Global Nick
            #
            # WA with name parameters to pull up more extensive information about the direction
            # Highest Occupants (since last reboot), Last Visited, Last Busy (3+) etc. (more ideas here)
            table.add_header('|wOcc', '|wLocation', '|wAvg Time', '|cTop 3 Active', '|gDirections')
            table.reformat_column(0, width=4, align='l')
            table.reformat_column(1, width=25, align='l')
            table.reformat_column(2, width=6, align='l')
            table.reformat_column(3, width=16, pad_right=1, align='l')
            table.reformat_column(4, width=20, align='l')
            locations = {}  # Create an empty dictionary to gather locations information.
            sessions_using_puppets = self.option_sort(sessions_using_puppets, 'alpha')
            for session in sessions_using_puppets:  # Go through connected list and see who's where.
                character = session.get_puppet()
                if character.location not in locations:
                    locations[character.location] = []
                locations[character.location].append(character)  # Build the list of who's in a location
            for place in locations:
                location = place.get_display_name(you) if place else (settings.NOTHINGNESS + '|n')
                table.add_row(len(locations[place]), location, '?',
                              ', '.join(each.get_display_name(you) for each in locations[place]),
                              '')  # TODO - Directions to location
        elif cmd == 'ws':
            my_character = self.caller.get_puppet(self.session)
            if not (my_character and my_character.location):
                self.msg("You can't see anyone here.")
                return
            table.add_header('|wCharacter', '|wOn for', '|wIdle')
            table.reformat_column(0, width=45, align='l')
            table.reformat_column(1, width=8, align='l')
            table.reformat_column(2, width=7, pad_right=1, align='r')
            for element in my_character.location.contents:
                if not element.has_account:
                    continue
                delta_cmd = time.time() - max([each.cmd_last_visible for each in element.sessions.all()])
                delta_con = time.time() - min([each.conn_time for each in element.sessions.all()])
                name = element.get_display_name(you)
                type = element.db.messages and element.db.messages.get('species') or ''
                gend = element.db.messages and element.db.messages.get('gender') or ''
                fill = ' ' if gend else ''
                table.add_row(name + ', ' + gend.lower() + fill + type if type else name,
                              utils.time_format(delta_con, 0), utils.time_format(delta_cmd, 1))
        elif cmd == 'what' or cmd == 'wot':
            session_list = self.option_sort(sessions_using_puppets, 'idle', True)
            table.add_header('|wCharacter  - Doing', '|wIdle')
            table.reformat_column(0, width=72, align='l')
            table.reformat_column(1, width=7, align='r')
            for session in session_list:
                character = session.get_puppet()
                if not session.logged_in or not character:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                doing = character.get_display_name(you, pose=True)
                table.add_row(doing, utils.time_format(delta_cmd, 1))
        else:  # Default to displaying who
            if show_session_data:  # privileged info shown to Immortals and higher only when not quelled
                table.add_header('|wCharacter', '|wAccount', '|wQuell', '|wCmds', '|wProtocol', '|wAddress')
                table.reformat_column(0, align='l')
                table.reformat_column(1, align='r')
                table.reformat_column(2, width=7, align='r')
                table.reformat_column(3, width=6, pad_right=1, align='r')
                table.reformat_column(4, width=11, align='l')
                table.reformat_column(5, width=16, align='r')
                for session in session_list:
                    account = session.get_account()
                    puppet = session.get_puppet()
                    address = isinstance(session.address, tuple) and session.address[0] or session.address
                    table.add_row(puppet.get_display_name(you) if puppet else 'None',
                                  account.get_display_name(you),
                                  '|gYes|n' if account.attributes.get('_quell') else '|rNo|n',
                                  session.cmd_total, session.protocol_key, address)
            else:  # unprivileged info shown to everyone, including Immortals and higher when quelled
                session_list = self.option_sort(sessions_using_puppets, 'alpha')
                table.add_header('|wCharacter', '|wOn for', '|wIdle')
                table.reformat_column(0, width=40, align='l')
                table.reformat_column(1, width=8, align='l')
                table.reformat_column(2, width=7, align='r')
                for session in session_list:
                    if not session.logged_in:
                        continue
                    character = session.get_puppet()
                    if not character:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    table.add_row(character.get_display_name(you), utils.time_format(delta_conn, 0),
                                  utils.time_format(delta_cmd, 1))
        account_count = (SESSIONS.account_count())
        is_one = account_count == 1
        string = '%s' % 'A' if is_one else str(account_count)
        string += ' single ' if is_one else ' unique '
        plural = ' is' if is_one else 's are'
        string += 'account%s logged in.' % plural
#        self.msg(unicode(table))
        self.msg(table)
        self.msg(string + notice)

    def option_sort(self, to_sort, sort_type='alpha', reverse=False):
        opt = self.switches
        if not (sort_type == 'alpha' and 'alpha' in opt):
            to_sort = sorted(to_sort, reverse=not ('reverse' in opt and reverse),
                             key=lambda sess: sess.get_puppet().key.lower())
        elif not (sort_type == 'on' and 'on' in opt):
            pass
        elif not (sort_type == 'idle' and 'idle' in opt):
            pass
        return to_sort
