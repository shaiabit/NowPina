# -*- coding: utf-8 -*-
from commands.command import MuxCommand
from evennia.utils import utils, search
from django.conf import settings


class CmdHome(MuxCommand):
    """
    Takes you to your home, if you have one. If you're already home,
    takes you to your home room. home/set will show you where your
    home is set, or provide a what and where to set its home.
    home/here will set your home here, if the location allows it.
    Usage:
      home[/option]
      sweep <object>
      abode
    Options:
    /set <obj> [=||to home_location]  views or sets <obj>'s home location.
    /sweep <obj>  send obj home. (same as using sweep command)
    /here  sets current character's home to current location (same as abode command)
    /room  returns a character to its home room (same as room command)
    
    The "home" location is a "safety" location for objects; they will be
    moved there if their current location ceases to exist. All objects
    should always have a home location for this reason.
    It is also a convenient target of the "home" command.
    """
    key = 'home'
    aliases = ['sweep', 'abode', 'room']
    switch_options = ('set', 'sweep', 'here', 'room')
    locks = 'cmd:all()'
    arg_regex = r"^/|\s|$"
    help_category = 'Travel'
    account_caller = True
    rhs_split = ('=', ' to ')

    def func(self):
        """Implement the command"""
        you = self.character
        account = self.account
        cmd = self.cmdstring
        opt = self.switches
        args = self.args
        if 'sweep' in cmd:  # Command to send something home
            opt.append('sweep')
        if 'abode' in cmd:  # Command to set home
            opt.append('here')
        if 'room' in cmd:  # Command to go to room
            opt.append('room')
        room = you.db.objects['home'] if you.db.objects and you.db.objects.get('home', False) else you.home
        home = room if 'room' in opt else you.home
        abode = 'here' in opt
        if 'room' in opt or not (opt or args):  # Command to go home or to room
            if not home:
                you.msg('You have no home yet.')
            else:
                if home == you.location:
                    if home is room:
                        you.msg('You are already home, which is the same as your home room.')
                        return
                    else:
                        you.msg('You are already home. Sending you to your home room...')
                        home = room
                you.msg("There's no place like home ...")
                you.move_to(home, use_destination=False)
        else:
            if not args:  # If nothing is specified to send home, then
                obj = you  # send you home
            else:
                afar = account.check_permstring('helpstaff')  # helpstaff can sweep from afar.
                obj = you.search(self.lhs, global_search=afar)  # send something else home
            if not obj or not obj.location:  # Tangibles in nothingness remain there
                if obj:
                    self.msg('{} remains in {}.'.format(obj.get_display_name(you), settings.NOTHINGNESS))
                return
            if 'sweep' in opt:  # If the option is sweeping,
                home = obj.home  # then something is going to its home
                if not home:  # (assuming it has a home)
                    you.msg('%s has no home yet.' % obj.get_display_name(account))
                elif home == obj.location:
                    you.msg('%s is already home!' % obj.get_display_name(account))
                elif obj is not you and not account.check_permstring('helpstaff')\
                        and not obj.access(account, 'puppet') and not obj.access(you, 'control')\
                        and not obj.location.access(you, 'control'):
                    you.msg("You do not have access to send {} home.".format(obj.get_display_name(account)))
                    return
                else:
                    if obj.db.worn:  # If object is being worn, do not send anywhere
                        you.msg('%s is still being worn.' % obj.get_display_name(account))
                        return
                    going_home = "There's no place like home ... ({} is sending you home.)"
                    obj.msg(going_home.format(you.get_display_name(obj)))
                    if you.location:
                        you.location.msg_contents('%s%s|n sends %s%s|n home.'
                                                  % (you.STYLE, you.key, obj.STYLE, obj.key))
                    was = obj.location
                    obj.move_to(home, use_destination=False)
                    if you.location != was:
                        source_location_name = was.get_display_name(you) if was else (settings.NOTHINGNESS + '|n')
                        you.msg("%s left %s and went home to %s."
                                % (obj.get_display_name(you), source_location_name, home.get_display_name(you)))
                return
            if not self.rhs and not abode:  # just view the destination set as home
                if obj != you and not account.check_permstring('helpstaff') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wHelpstaff|n or higher power to view the home of %s."
                            % obj.get_display_name(account))
                    return
                home = obj.home
                if not home:
                    string = "%s has no home location set!" % obj.get_display_name(you)
                else:
                    string = "%s's current home is %s." % (obj.get_display_name(you), home.get_display_name(you))
            else:  # set/change a home location
                if obj != you and not account.check_permstring('mage') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wmage|n or higher powers to change the home of %s." % obj)
                    return
                if self.rhs and not abode:
                    new_home = you.search(self.rhs, global_search=True)
                else:
                    new_home = you.location
                if not new_home:
                    return
                old_home = obj.home
                obj.home = new_home
                obj_name = obj.get_display_name(you)
                old_home_name = old_home.get_display_name(you)
                if old_home:
                    if old_home is new_home:
                        string = "%s's home location is already set to %s." % (obj_name, old_home_name)
                    else:
                        string = "%s's home location was changed from %s to %s." % (obj_name, old_home_name,
                                                                                    new_home.get_display_name(you))
                else:
                    string = "%s' home location was set to %s." % (obj_name, new_home.get_display_name(you))
            you.msg(string)
