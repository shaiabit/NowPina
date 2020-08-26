# -*- coding: utf-8 -*-
"""
Characters are (by default) Objects setup to be puppeted by accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.
"""
from evennia import DefaultCharacter
from typeclasses.tangibles import Tangible
from evennia.utils.utils import lazy_property
from typeclasses.traits import TraitHandler
from world.helpers import make_bar, mass_unit
from evennia.contrib.clothing import get_worn_clothes
from evennia.utils import list_to_string
from evennia.utils import ansi
# from evennia.utils.utils import delay  # Delay a follower's arrival after the leader
from evennia.comms.models import ChannelDB, Msg  # To find and
from evennia.comms.channelhandler import CHANNELHANDLER  # Send to public channel
from django.conf import settings
import time  # Check time since last visit


class Character(DefaultCharacter, Tangible):
    """
    The Character defaults to implementing some of its hook methods with the
    following standard functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(account) -  when account disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before account re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room
    """
    STYLE = '|c'

    def at_object_creation(self):
        """Initialize a newly-created Character"""
        super(Character, self).at_object_creation()
        new_locks = ';'.join(
            ('drop:all(); mail:all();view:all();follow:all()',
             'examine:perm(helpstaff)', 'tell:perm(wizard)',
             'delete:perm(immortal)', 'call:false(); get:false()'))
        self.locks.add(new_locks)  # Add these new locks to the character
        # Check to see if Character has an object dictionary
        if not self.db.objects:   # Prime non-existent objects attribute
            self.db.objects = {}  # with empty list
        # Check to see if Character has a home room set.
        home_room = self.db.objects.get('home')
        if not home_room:  # if self has no home room,
            home_room = self.assign_room()  # call the assign_room method.
            self.db.objects['home'] = home_room  # Set the character's home room
        self.db.last_room = self.home  # Set back point to global default home
        self.home = home_room  # Set home to home room
        self.ndb.home_room = home_room  # Store for user later.

    def assign_object(self):
        """
        This is where the new character is given a choice to receive one of several
        new object types, limit one per character. Offer void where prohibited.
        """
        #  piece of clothing (or jewelry), dice, canister, weapon, furniture, or plush/soft sculpt critter.
        choices = ['wearable (jewelry/clothing', 'deluxe RP dice',
                   'small weapon for defense', 'furnishing for your room',
                   'plush or soft sculpt huggable creature']

        def scrambled(orig):
            """
            Given an iterable, returns a shuffled list of it.
            """
            import random  # used for the "scrambled" method.
            dest = orig[:]
            random.shuffle(dest)
            return dest

        self.msg("A {} lands beside you in {}!".format(scrambled(choices).pop(),  # Deal a random choice card.
                 self.location.get_display_name(self)))
        # This is an initial test. Choice will be dispensed from a vending machine later.

    def assign_room(self):
        """
        Spawn a new home room for this character.
        Set locks:  set "owner" to edit/control lock,
        set owner's home there, (self.home = there)
        set owner's home room there.
            (self.db.objects['home'] = there)
        Move owner there?
        """
        # Spawn a new room with locks:
        home_room_name = self.name + "'s place"
        home_room_desc = settings.HOME_ROOM_DESC
        home_room_locks = 'control:id({0}) or perm(wizard);edit:id({0}) ' \
                          'or perm(helpstaff)'.format(self.id)
        home_room_tags = [('private', 'flags', True)]
        home_room = {'typeclass': 'typeclasses.rooms.Room', 'key': home_room_name, 'desc': home_room_desc,
                     'locks': home_room_locks, 'tags': home_room_tags}
#        from evennia.utils.spawner import spawn  # Import the spawn utility just before using it.
        from evennia.prototypes.spawner import spawn
        room = spawn(home_room)  # Calling spawn utility to create the home room.
        return room[0]  # Return the first (and only) object created, the room.

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """
        if not self.location:  # Always allow moving from Nothingness
            return True
        if destination == self.location:  # Prevent move into same room character is already in.
            return False
        if self.nattributes.has('mover'):  # Allow move when being moved by something.
            return True
        if self.db.locked:  # Prevent leaving a room while still sitting.
            self.msg("\nYou're still sitting.")  # stance, prep, obj
            return False  # Object is supporting something; do not move it
        elif self.traits.health and not self.location.tags.get('past', category='realm')\
                and self.traits.health.actual <= 0:  # Prevent move while incapacitated.
            self.msg("You can't move; you're incapacitated!")  # Type 'home' to TODO:
            # go back home and recover, or wait for a healer to come to you.")
            return False
        if self.db.Combat_TurnHandler:  # Prevent move while in combat.
            self.caller.msg("You can't leave while engaged in combat!")
            return False
        if self.attributes.has('riders') and self.db.riders and self.location:  # Test list of riders.
            self.ndb.riders = []
            if self.db.settings and 'carry others' in self.db.settings and self.db.settings['carry others'] is False:
                return True  # Character has riders, but does not want to carry them.
            for each in self.db.riders:
                if each.location == self.location:
                    each.ndb.mover = self
                    if not (each.has_account and each.at_before_move(destination)):
                        continue
                    if each.db.settings and 'carry others' in each.db.settings and each.db.settings['carry others']\
                            is False:
                            continue
                    self.ndb.riders.append(each)
                    self.location.at_object_leave(each, destination)
        return True

    def at_after_move(self, source_location):
        """Store last location and room then trigger the arrival look after a move. Reset doing to default."""
        if self.db.messages and self.db.messages.get('location'):
            loc_name = self.location.get_display_name(self, plain=True)
            self.msg(self.db.messages.get('location') + loc_name)
        if source_location:  # Is "None" when moving from Nothingness. If so, do nothing.
            self.ndb.last_location = source_location
            # If the last room was a private room, no going back.
            if not (source_location.destination or source_location.tags.get('private', category='flags')):
                self.db.last_room = source_location
        if self.location:  # Things to do after the character moved somewhere
            if self.db.messages:
                self.db.messages['pose'] = self.db.messages.get('pose_default', None)  # Reset room pose after moving.
            if self.location.access(self, 'view'):  # No need to look if moving into Nothingness, locked from looking
                if not self.db.settings or self.db.settings.get('look arrive', default=True):
                    self.msg(text=(self.at_look(self.location), dict(type='look', window='room')))
            followers = self.db.followers
            if source_location and (not not followers) and self.ndb.exit_used:
                for each in source_location.contents:
                    if not each.has_account or each not in followers or not self.access(each, 'view'):
                        continue  # no account, not on follow list, or can't see character to follow, then do not follow
                    # About to follow - check if follower is riding something:
                    riding = False
                    for thing in source_location.contents:
                        if thing == each or not thing.db.riders or each not in thing.db.riders:
                            continue
                        riding = True
                    if not riding:
                        print('<%s> %s' % (each, self.ndb.exit_used))
                        each.execute_cmd(self.ndb.exit_used)
        return source_location

    def announce_move_from(self, destination):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.
        Args:
            destination (Object): The place that the object is going
        """
        here = self.location
        if not here:
            return
        direction_name = (' |lc%s|lt|530%s|n|le' % (self.ndb.moving_to,
                                                    self.ndb.moving_to)) if self.ndb.moving_to else ''
        # TODO - if character leaving is invisible to viewer and all riders are invisible, then no message sent
        # to viewer, otherwise anyone invisible is listed as "Someone"
        for viewer in here.contents:
            if viewer == self:
                continue
            name = self.get_display_name(viewer, color=False)
            loc_name = self.location.get_display_name(viewer)
            dest_name = destination.get_display_name(viewer)
            message = ['|r%s' % name]
            if self.ndb.riders and len(self.ndb.riders) > 0:  # Plural exit message: Riders
                if len(self.ndb.riders) > 1:
                    for rider in self.ndb.riders[:-1]:
                        message.append('|n, |r' + rider.get_display_name(viewer, color=False))
                message.append(' and |r%s|n are ' % self.ndb.riders[-1].get_display_name(viewer, color=False))
            else:  # Singular exit message: no riders
                message.append(' is ')
            message.append('leaving %s, heading%s for %s.' % (loc_name, direction_name, dest_name))
            viewer.msg(''.join(message))

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.
        Args:
            source_location (Object): The place we came from
        """
        here = self.location
        if not source_location and self.location.has_account:
            # This was created from nowhere and added to a account's
            # inventory; it's probably the result of a create command.
            here.msg('You now have {} in your possession.'.format(self.get_display_name(here)))
            return
        direction_name = ('|lc%s|lt|530%s|n|le' % (self.ndb.moving_from,
                                                   self.ndb.moving_from)) if self.ndb.moving_from else ''
        for viewer in here.contents:
            if viewer == self:
                continue
            src_name = settings.NOTHINGNESS
            if source_location:
                src_name = source_location.get_display_name(viewer)
            message = ['|g%s' % self.get_display_name(viewer, color=False)]
            if here:
                depart_name = here.get_display_name(viewer)
            else:
                depart_name = settings.NOTHINGNESS
            if self.ndb.riders and len(self.ndb.riders) > 0:
                if len(self.ndb.riders) > 1:
                    message.append(', |g' + '%s' % '|n, |g'.join(rider.get_display_name(viewer, color=False))
                                   for rider in self.ndb.riders[:-1])
                    message.append('|n and |g%s|n arrive ' % self.ndb.riders[-1].get_display_name(viewer, color=False))
                else:
                    message.append(' and |g%s|n arrive ' % self.ndb.riders[-1].get_display_name(viewer, color=False))
            else:
                message.append(' arrives ')
            if direction_name:
                message.append('to %s|n from the %s from %s|n.' % (depart_name, direction_name, src_name))
            else:
                message.append('to %s|n from %s|n.' % (depart_name, src_name))
            viewer.msg(''.join(message))
        if self.ndb.riders and len(self.ndb.riders) > 0:
            for each in self.ndb.riders:
                success = each.move_to(here, quiet=True, emit_to_obj=None, use_destination=False,
                                       to_none=False, move_hooks=False)
                # If moved to grid room, write location onto character here
                # If moved from grid room, save old location for possible return
                each.ndb.grid_loc, last = self.ndb.grid_loc, each.ndb.grid_loc
                if not success:
                    self.msg('|r%s|n did not arrive.' % each.get_display_name(self, color=False))
                    # If failed move to grid room, re-write location, last location used for going back.
                    if last:
                        self.ndb.grid_loc = last
                    each.nattributes.remove('mover')
                    self.ndb.riders.remove(each)
                    continue
            for each in self.ndb.riders:
                here.at_object_receive(each, source_location)
                each.at_after_move(source_location)
                each.nattributes.remove('mover')
            self.nattributes.remove('riders')
        if self.db.settings and not self.db.settings.get('look arrive', default=True):
            awake = (con for con in self.location.contents if con != self
                     and con.has_account and con.access(self, 'view'))
            awake_list = ", ".join(a.get_display_name(self, mxp='sense %s' % a.get_display_name(
                self, plain=True), pose=True) for a in awake)
            awake_list = (' Awake here: ' + awake_list) if len(awake_list) > 0 else ''
            self.msg('|/|gArriving at %s.%s'
                     % (self.location.get_display_name(self, mxp='look here'), awake_list.replace('.,', ';')))
        self.nattributes.remove('moving_to')
        self.nattributes.remove('moving_from')

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        account<->Object links have been established.
        NOTES: self.msg() or caller.msg(..., session=self.session)
        sends to the session actually triggering the command.
        account.sessions.all() exclude self.session could send
        to all but the current session.
        `self.account` and `self.sessions.get()` retrieves
        account and sessions at this point; the last entry in the
        list from `self.sessions.get()` is the latest Session puppeting this Object.
        """
        sessions = self.sessions.get()
        session = sessions[-1] if sessions else None
        if len(sessions) == 1:  # Skip re-stamping if the object is already puppeted.
            # After an account connects to a character, set the character's timestamp on:
            # Add object to "puppeted" attribute dictionary on self, keyed by self.account.
            # Value is (timestamp on, timestamp off, puppet_count)
            now = int(time.time())
            last_entry = (self.db.puppeted and self.db.puppeted.get(self.account)) or (now, now, 0)
            puppet_count = (last_entry[2] + 1)
            if self.db.puppeted:
                self.db.puppeted[self.account] = (now, None, puppet_count)
            else:
                self.db.puppeted = {self.account: (now, None, puppet_count)}
            channel = ChannelDB.objects.channel_search('Public')
            if channel and channel[0]:
                channel[0].msg('|c%s |gis now active.' % self.key, keep_log=True)
            text = 'fades into view' if self.location != self.home else 'awakens'
            for each in self.location.contents:
                if not each.access(self, 'view') or each is self:
                    continue
                each.msg('|g%s|n %s.' % (self.get_display_name(each, color=False), text), from_obj=self)
        is_somewhere = self.location is not None
        if self.db.messages and self.db.messages.get('location'):
            loc_name = self.location.get_display_name(self, plain=True)
            self.msg(self.db.messages.get('location') + loc_name)
        if session:
            session.msg('\nYou assume the role of: %s\n' % self.get_display_name(self, pose=is_somewhere))
            if is_somewhere:  # if puppet is somewhere
                session.msg(self.at_look(self.location))  # look to see surroundings
            session.msg('\nChecking for new mail in your mailbox. (@mail # to read message #)')
            self.account.execute_cmd('@mail')

    def at_post_unpuppet(self, account, session=None):
        """
        Store characters in Nothingness when the account goes ooc/logs off,
        when characters are left in a room that is not home. Otherwise
        character objects remain in the room after accounts leave.
        Args:
            account (account): The account object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if self.has_account:  # if there's still a session controlling ...
            return  # ... then there's nothing more to do.
        if self.location:
            # reason = ['Idle Timeout', 'QUIT', 'BOOTED', 'Lost Connection']  # TODO
            at_home = self.location == self.home
            text = 'sleeps' if at_home else 'fades from view'
            for each in self.location.contents:
                if not each.access(self, 'view'):
                    continue
                each.msg('|r%s|n %s.' % (self.get_display_name(each, color=False), text), from_obj=self)
            self.db.prelogout_location = self.location
            if not self.has_account:  # if no sessions control it anymore...
                # After an account disconnects from a character, set the character's timestamp off:
                # Add object to "puppeted" attribute dictionary on self, keyed by account.
                # Value is (timestamp on, timestamp off, puppet_count)
                now = int(time.time())
                last_entry = (self.db.puppeted and self.db.puppeted.get(account)) or (now, now, 0)
                if self.db.puppeted:
                    self.db.puppeted[account] = (last_entry[0], now, last_entry[2])
                else:
                    self.db.puppeted = {account: (last_entry[0], now, last_entry[2])}
                channel = ChannelDB.objects.channel_search('Public')
                if channel and channel[0]:
                    channel[0].msg('|c%s |ris now inactive.' % self.key, keep_log=True)
                if not at_home:  # ... and its not home...
                    self.location = None  # store in Nothingness.

    def process_sdesc(self, sdesc, obj, **kwargs):
        """
        Allows to customize how your sdesc is displayed (primarily by changing colors).
        Args:
            sdesc (str): The sdesc to display.
            obj (Object): The object to which the adjoining sdesc
                belongs (can be yourself).

        Returns:
            sdesc (str): The processed sdesc ready
                for display.
        """
        if self.check_permstring('mage'):
            return '%s%s|n [|[G%s|n]' % (obj.STYLE, sdesc, obj.key)
        else:
            return '%s%s|n' % (obj.STYLE, sdesc)

    def process_recog(self, recog, obj, **kwargs):
        """
        Allows to customize how a recog string is displayed.
        Args:
            recog (str): The recog string. It has already been
                translated from the original sdesc at this point.
            obj (Object): The object the recog:ed string belongs to.
                This is not used by default.
        Returns:
            recog (str): The modified recog string.
        """
        return self.process_sdesc(recog, obj)

    def get_pronoun(self, regex_match):
        """
        Get pronoun from the pronoun marker in the text. This is used as
        the callable for the re.sub function.
        Args:
            regex_match (MatchObject): the regular expression match.
        Notes:
            - `|s`, `|S`: Subjective form: he, she, it, He, She, It
            - `|o`, `|O`: Objective form: him, her, it, Him, Her, It
            - `|p`, `|P`: Possessive form: his, her, its, His, Her, Its
            - `|a`, `|A`: Absolute Possessive form: his, hers, its, His, Hers, Its
        """

        _GENDER_PRONOUN_MAP = {'male': {'s': 'he', 'o': 'him', 'p': 'his', 'a': 'his'},
                               'female': {'s': 'she', 'o': 'her', 'p': 'her', 'a': 'hers'},
                               'neutral': {'s': 'it',  'o': 'it', 'p': 'its', 'a': 'its'}}

        # _RE_GENDER_PRONOUN = re.compile(r'[^\|]+(\|s|S|o|O|p|P|a|A)')

        typ = regex_match.group()[2]  # "s", "O" etc
        gender = self.attributes.get('gender', default='neutral')
        gender = gender if gender in ('male', 'female', 'neutral') else 'neutral'
        pronoun = _GENDER_PRONOUN_MAP[gender][typ.lower()]
        return pronoun.capitalize() if typ.isupper() else pronoun

    def return_appearance(self, viewer):
        """This formats a description. It is the hook a 'look' command should call.
        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return ''
        if not viewer.is_typeclass('typeclasses.accounts.Account'):
            viewer = viewer.account  # make viewer reference the account object
        char = viewer.puppet
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and
                   con.access(viewer, 'view'))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_account:
                users.append(con)
            else:
                if not con.db.worn:
                    things.append(con)
        message = ['\n%s' % self.get_display_name(viewer, mxp='sense %s' % self.get_display_name(viewer, plain=True))]
        if self.location and self.location.tags.get('rp', category='flags'):
            pose = self.db.messages and self.db.messages.get('pose', None)
            message.append(' %s' % pose or '')
        if self.traits.mass and self.traits.mass.actual > 0:
            message.append(' |y(%s)|n ' % mass_unit(self.get_mass()))
        if self.traits.health:  # Add character health bar if character has health.
            gradient = ['|[300', '|[300', '|[310', '|[320', '|[330', '|[230', '|[130', '|[030', '|[030']
            health = make_bar(self.traits.health.actual, self.traits.health.max, 20, gradient)
            message.append(' %s\n' % health)
        else:
            message.append('\n')
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            message.append('%s' % desc)
        elif desc_brief:
            message.append('%s' % desc_brief)
        else:
            message.append('A shimmering illusion shifts from form to form.')
        # ---- Allow clothes wearing to be seen
        worn_string_list = []
        clothes_list = get_worn_clothes(self, exclude_covered=True)
        # Append worn, uncovered clothing to the description
        for garment in clothes_list:
            if garment.db.worn is True:  # If 'worn' is True,
                worn_string_list.append(garment.name)  # just append the name.
            # Otherwise, append the name and the string value of 'worn'
            elif garment.db.worn:
                worn_string_list.append("%s %s" % (garment.name, garment.db.worn))
        if worn_string_list:  # Append worn clothes.
            message.append('|/|/%s is wearing %s.' % (self, list_to_string(worn_string_list)))
        # ---- List things carried (excludes worn things)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer) for t in things)
            message.append('\n|wYou see:|n ' + user_list + ut_joiner + item_list)
        # ---- Look Notify system:
        if self != char:
            if not (self.db.settings and 'look notify' in self.db.settings
                    and self.db.settings['look notify'] is False):
                self.msg("%s just looked at you." % char.get_display_name(self))
        return ''.join(message)


class NPC(Character):
    """Uses Character class as a starting point."""
    STYLE = '|m'

    def at_object_creation(self):
        """Initialize a newly-created NPC"""
        super(NPC, self).at_object_creation()
        pass

    def assign_room(self):
        return self.home  # NPC home is default.

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        account<->Object links have been established.
        """
        self.msg("\nYou assume the role of %s.\n" % self.get_display_name(self))
        self.msg(self.at_look(self.location))
        if self.ndb.new_mail:
            self.msg('|/You have new mail in your %s mailbox.|/' % self.home.get_display_name(self))
        if self.sessions.count() > 1:  # Show as pose if NPC already has a account.
            for each in self.location.contents:
                if not each.access(self, 'view'):
                    continue
                each.msg("%s looks more awake." % self.get_display_name(each), from_obj=self)
        else:
            # After an account connects to a character, set the NPC's timestamp on:
            # Add object to "puppeted" attribute dictionary on self, keyed by self.account.
            # Value is (timestamp on, timestamp off, puppet_count)
            now = int(time.time())
            last_entry = (self.db.puppeted and self.db.puppeted.get(self.account)) or (now, now, 0)
            puppet_count = (last_entry[2] + 1)
            if self.db.puppeted:
                self.db.puppeted[self.account] = (now, None, puppet_count)
            else:
                self.db.puppeted = {self.account: (now, None, puppet_count)}
            for each in self.location.contents:
                if not each.access(self, 'view'):
                    continue
                each.msg("|g%s|n awakens." % self.get_display_name(each, color=False), from_obj=self)

    def at_post_unpuppet(self, account, session=None):
        """
        We store the character when the account goes ooc/logs off,
        when the character is left in a public or semi-public room.
        Otherwise the character object will remain in the room after
        the account logged off ("headless", so to say).
        Args:
            account (Account): The account object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if self.location:
            if self.has_account:  # Show as pose if NPC still being puppeted.
                for each in self.location.contents:
                    if not each.access(self, 'view'):
                        continue
                    each.msg("%s looks sleepier." % (self.get_display_name(each)), from_obj=self)
            else:  # Show as sleeping if NPC has no account logged in.
                # After an account disconnects from a character, set the NPC's timestamp off:
                # Add object to "puppeted" attribute dictionary on self, keyed by account.
                # Value is (timestamp on, timestamp off, puppet_count)
                now = int(time.time())
                last_entry = (self.db.puppeted and self.db.puppeted.get(account)) or (now, now, 0)
                if self.db.puppeted:
                    self.db.puppeted[account] = (last_entry[0], now, last_entry[2])
                else:
                    self.db.puppeted = {account: (last_entry[0], now, last_entry[2])}
                for each in self.location.contents:
                    if not each.access(self, 'view'):
                        continue
                    each.msg("|r%s|n sleeps." % self.get_display_name(each, color=False), from_obj=self)
            self.db.prelogout_location = self.location




class ColorlessCharacter(Character, Tangible):
    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        super().msg(text=ansi.strip_ansi(text), from_obj=from_obj, session=session, options=options **kwargs)

