# -*- coding: utf-8 -*-
from commands.command import MuxCommand
from world.helpers import escape_braces, substitute_objects
from evennia.utils import ansi


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.
    pose, :, ;, do, pp
    Usage:
      pose[/option] <pose text>
      pose[/option]'s <pose text>
      do[/option] <pose text>
      do[/option] <target>=<pose text>
      pp[/option] <parse> = <pose text>
    Options:
    /ooc  (Out-of-character to the room or channel.)
    /magnet  (Show which characters remove name/pose space.)
    /do or do, rp, doing  (Pose and set room-pose/doing message.)
      Additional options for do, rp, doing command version of pose:
      /reset   (Reset the current room pose to use default setting)
      /default (Set the default room pose for all rooms, all times)
      /quiet or /silent (Update doing, but do not pose)

    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.
      > do is standing by the tree, smiling.
      Current room pose set to "Rulan is standing by the tree, smiling."
      > do stapler=is out of staples.
      Current room pose set to "Orange Swingline stapler is out of staples."
    """
    # > ppose get anvil = strains to lift the anvil.
    # > Werewolf strains to lift the anvil.
    # ==> Werewolf takes the anvil.
    # (optional success message if anvil can be lifted.)
    key = 'pose'
    aliases = ['p:', 'pp', 'ppose', ':', ';', 'rp', 'do', 'doing']
    arg_regex = None
    options = ('ooc', 'magnet', 'do', 'reset', 'default', 'quiet', 'silent')
    locks = 'cmd:all()'
    account_caller = True

    def set_doing(self, setter, pose, target=None, default=False):
        """

        Args:
            self:  (Cmd)
            setter: (Tangible) object setting pose
            pose: (str) pose to set on object
            target: (Tangible) object to pose
            default: (bool) Setting default

        Returns:
            pose, pose_default
        """
        if not target:
            target = setter
        if not target.db.messages:
            target.db.messages = dict(pose='', pose_default='')
        if target.db.messages.get('pose') is None:
            target.db.messages['pose'] = ''
        if target.db.messages.get('pose_default') is None:
            target.db.messages['pose_default'] = ''
        if not setter:
            return target.db.messages['pose'], target.db.messages['pose_default']
        if not target.access(setter, 'edit') and setter is not target:  # target being accessed/edited by setter
            setter.msg('You have no permission to edit %s.' % target.get_display_name(setter))
            return None
        if not pose:
            setter.msg('Wot?')
            return
        set_this = 'pose' if not default else 'pose_default'
        target.db.messages[set_this] = pose
        return target.db.messages['pose'], target.db.messages['pose_default']

    def func(self):
        """Basic pose, power pose, room posing - all in one"""
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        lhs, rhs = self.lhs, self.rhs
        sess = self.session
        char = self.character
        account = self.account
        here = char.location if char else None
        power = True if cmd in ('ppose', 'pp', 'p:') else False
        raw_pose = rhs if rhs and cmd == 'do' or power else args
        raw_pose = substitute_objects(raw_pose, char)
        non_space_chars = ['®', '©', '°', '·', '~', '@', '-', "'", '’', ',', ';', ':', '.', '?', '!', '…']
        magnet = True if raw_pose and raw_pose[0] in non_space_chars or cmd == ";" else False
        doing = True if 'do' in cmd or 'rp' in cmd else False
        pose = ('' if magnet else '|_') + (ansi.strip_ansi(raw_pose) if doing else raw_pose)
        # ---- Setting Room poses as a doing message ----------
        if doing:  # Pose will have no markup when posing on the room, to minimize shenanigans.
            target = char  # Initially assume the setting character is the target.
            if not args and 'reset' not in opt:
                has_pose = char.db.messages and char.db.messages.get('pose')
                if has_pose:  # If target has poses set, display them to the setter.
                    char.msg("Current pose reads: '%s'" % target.get_display_name(char, pose=True))
                    default_pose = target.db.messages and target.db.messages.get('pose_default') or None
                    if default_pose:
                        char.msg('Default pose is \'%s%s\'' % (char.get_display_name(char), default_pose))
                    else:
                        char.msg('Default pose not set.')
                else:
                    char.msg('No pose has been set.|/Usage: rp <pose-text> OR pose <obj> = <pose-text>')
                return
            if len(pose) > 60:  # Pose length in characters, not counting the poser's name.
                char.msg('Your pose is too long.')
                return
            if rhs:  # pose something else other than self.
                target = char.search(lhs)  # Search for a reference to the target.
                if not target:
                    return
                if pose:
                    self.set_doing(char, pose, target)  # Try to set the pose of the target.
            else:  # pose self.
                target = char
            if 'reset' in opt:  # Clears current temp doing, reverts it to default.
                pose = target.db.messages and target.db.messages.get('pose_default', '')
                if not target.db.messages:
                    target.db.messages = {}
                target.db.messages['pose'] = pose
            elif 'default' in opt:  # Sets doing pose default.
                self.set_doing(char, pose, target, True)  # True means "set default", not temp doing.
                char.msg("Default pose is now: '%s%s'" % (target.get_display_name(char), pose))
                return  # Nothing more to do. Default never poses to room, just sets doing message.
            elif not rhs:
                self.set_doing(char, pose)  # Setting temp doing message on the setter...
                if args and not ('silent' in opt or 'quiet' in opt) and char is target:  # Allow set without posing
                    account.execute_cmd(';%s' % pose, session=sess)  # pose to the room like a normal pose would.
            char.msg("Pose now set to: '%s'" % target.get_display_name(char, pose=True))  # Display name with pose.
        else:  # ---- Action pose, not static Room Pose. ---------------------
            if '|/' in pose:
                pose = pose.split('|/', 1)[0]
            if 'magnet' in opt:
                char.msg("Pose magnet glyphs are %s." % non_space_chars)
            if not (here and char):
                if args:
                    account.execute_cmd('pub :%s' % pose, session=sess)
                else:
                    self.msg('Usage: pose <message>   to pose to public channel.')
                return
            if args:
                if power and self.rhs and 'o' not in self.switches:
                    char.ndb.power_pose = pose
                    account.execute_cmd(self.rhs, session=sess)
                else:
                    ooc = 'ooc' in self.switches
                    prepend_ooc = '[OOC] ' if ooc else ''
                    here.msg_contents(('%s{char}%s' % (prepend_ooc, escape_braces(pose)),
                                       {'type': 'pose', 'ooc': ooc}),
                                      from_obj=char, mapping=dict(char=char))
            else:
                account.execute_cmd('help pose', session=sess)
