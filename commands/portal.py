# -*- coding: utf-8 -*-
import evennia
from evennia.utils.utils import delay
from commands.command import MuxCommand
from evennia.server.sessionhandler import SESSIONS
from django.conf import settings


class CmdPortal(MuxCommand):
    """
    Open portal from object's location to yours, or location you specify.
    The portal forms after a slight delay and is, under some circumstances,
    one-way only.
    Usage:
      portal/option <target>
    Options:
    /quiet     Portal arrives quietly. Only you and target are notified.
    /only      Only the involved parties can use the portal.
    /in        Portal is one-way; into your location.
    /out       Portal is one-way; out from your location.
    Examples:
      summon/only Tria
      join Rulan
      meet/quiet LazyLion
    """
    key = 'portal'
    aliases = ['meet', 'join', 'summon']
    switch_options = ('quiet', 'silent', 'only', 'in', 'out', 'vanish')
    locks = 'cmd:pperm(denizen)'
    help_category = 'Travel'

    def func(self):
        """
            Performs the summon, accounting for in-world conditions.
            join: Implies one way portal to target
            summon: Implies one way portal to summoner
            meet: Implies two-way portal, both can meet.
        """

        char = self.character
        cmd = self.cmdstring
        loc = char.location
        account = self.account
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        opt = self.switches
        
        message_private = ' in a private room that does not allow portals to form.'

        if char and char.ndb.currently_moving:
            account.msg("You can not open a portal while moving. (|lcstop|lt|rStop|n|le, then try again.)")
            return
        if not args and 'vanish' not in opt:
            char.msg('Usage: {} <character or NPC>'.format(cmd))
            return
        session_list = SESSIONS.get_sessions()
        target = []
        # Check for private flag on source room. It must be controlled by summoner if private.
        if loc.tags.get('private', category='flags') and not loc.access(char, 'control'):
            char.msg('You are' + message_private)
            return
        # Check object pool filtered by tagged "pool" and located in None.
        obj_pool = [each for each in evennia.search_tag('pool', category='portal') if not each.location]
        print('Object pool total: %i' % len(obj_pool))
        if len(obj_pool) < 2:
            char.msg('Portals are currently out of stock or in use elsewhere.')
            return
        portal_enter, portal_exit = obj_pool[-2:]
        for session in session_list:
            if not (session.logged_in and session.get_puppet()):
                continue
            puppet = session.get_puppet()
            if lhs.lower() in puppet.get_display_name(char, plain=True).lower():
                target.append(puppet)
        if len(target) < 1:
            char.msg("Specific character name not found.")
            return
        elif len(target) > 1:  # Too many partial matches, try exact matching.
            char.msg("Unique character name not found.")
            return
        first_target = target[0]
        target = list(set(target))  # Remove duplicate character sessions
        target = first_target
        # Check for private flag on destination room. If so, check for in/out locks.
        there = target.location
        if there and there.tags.get('private', category='flags') and not there.access(char, 'control'):
            char.msg('Destination of portal is' + message_private)
            return
        # Check if A can walk to B, or B to A depending on meet or summon,
        # because sometimes a portal might not be needed.
        meet_message = 'You are being invited to meet {summoner} in {loc}.'
        join_message = 'You are being joined by {summoner} from {loc}.'
        summon_message = 'You are being summoned to {loc} by {summoner}.'
        message = meet_message if 'meet' in cmd else (summon_message if 'summon' in cmd else join_message)
        loc_name = loc.get_display_name(target)
        target_name = target.get_display_name(char)
        char_name = char.get_display_name(target)
        target.msg(message.format(summoner=char_name, loc=loc_name))
        target.msg('A portal should appear soon.')
        char.msg("You begin to open a portal connecting %s" % target_name + " and your location.")

        def open_portal():
            """Move inflatable portals into place."""
            # If in or out, join or summon, lock portals, depending.
            enter_lock, exit_lock = 'all()', 'all()'
            if 'only' in opt:
                enter_lock = 'id({}) OR id({})'.format(target.id, char.id)
                exit_lock = 'id({}) OR id({})'.format(target.id, char.id)
            if 'in' in opt or 'join' in cmd:
                enter_lock = 'none()'
            if 'out' in opt or 'summon' in cmd:
                exit_lock = 'none()'
            portal_enter.locks.add('enter:' + enter_lock)
            portal_exit.locks.add('enter:' + exit_lock)
            quiet = True if ('quiet' in opt or 'silent' in opt) else False
            portal_enter.move_to(target.location, quiet=quiet)
            if quiet:
                target.msg('{} quietly appears in {}.'.format(portal_enter.get_display_name(target), loc_name))
                char.msg('{} quietly appears in {}.'.format(portal_exit.get_display_name(char),
                                                            loc.get_display_name(char)))
            portal_exit.move_to(loc, quiet=quiet)

        delay(10, callback=open_portal)  # 10 seconds later, the portal (exit pair) appears.

        def close_portal():
            """Remove and store inflatable portals in Nothingness."""
            vanish_message = '|r{}|n vanishes into ' + settings.NOTHINGNESS + '.'
            for every in portal_enter.contents:
                every.move_to(target.location)
            for every in portal_exit.contents:
                every.move_to(loc)
            # if not quiet:
            if portal_enter.location:
                portal_enter.location.msg_contents(vanish_message.format(portal_enter))
                portal_enter.move_to(None, to_none=True)  # , quiet=quiet)
            if portal_exit.location:
                portal_exit.location.msg_contents(vanish_message.format(portal_exit))
                portal_exit.move_to(None, to_none=True)  # , quiet=quiet)

        delay(180, callback=close_portal)  # Wait, then move portal objects to the portal pool in Nothingness
