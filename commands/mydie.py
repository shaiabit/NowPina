# -*- coding: UTF-8 -*-
import random
from builtins import range
from commands.command import MuxCommand
from evennia import CmdSet
from random import randint


class MyDieCmdSet(CmdSet):
    key = 'dice'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the die object."""
        self.add(CmdMyDie())


class CmdMyDieDefault(MuxCommand):
    """Add command to the set - this set will be attached to the vehicle object (item or room)."""
    key = 'mydie'
    locks = 'cmd:all()'
    help_category = 'Game'
    player_caller = True

    def roll_dice(self, dicenum, dicetype, modifier=None, conditional=None, return_tuple=False):
        """many sided-dice roller"""
        dice_num = int(dicenum)
        dice_type = int(dicetype)
        rolls = tuple([randint(1, dice_type) for roll in range(dice_num)])
        result = sum(rolls)
        if modifier:  # make sure to check types well before eval
            mod, mod_value = modifier
            if mod not in ('+', '-', '*', '/'):
                raise TypeError("Non-supported dice modifier: %s" % mod)
            mod_value = int(mod_value)  # for safety
            result = eval("%s %s %s" % (result, mod, mod_value))
        outcome, diff = None, None
        if conditional:  # make sure to check types well before eval
            cond, cond_value = conditional
            if cond not in ('>', '<', '>=', '<=', '!=', '=='):
                raise TypeError("Non-supported dice result conditional: %s" % conditional)
            cond_value = int(cond_value)  # for safety
            outcome = eval("%s %s %s" % (result, cond, cond_value))  # True/False
            diff = abs(result - cond_value)
        if return_tuple:
            return result, outcome, diff, rolls
        else:
            return outcome if conditional else result


class CmdMyDie(CmdMyDieDefault):
    """
    Usage: 
      Mydie[/option] [die name] [= character names/face name]
    Options:
    /hidden - tells the room what die is being rolled but only show results to self.
    /secret - don't inform the room about either roll or result, only to self.
    /new - Create a new die with name set this die as current die to roll.
    /add - add a face to the die name or current die, if no name given.
    /del (or rem) - remove the last face [or named face] from the particular die.
    /list (or show)  - show all die faces.
    /shuffle  - show all die faces in a shuffled order.
    /multi <n> - roll die n times.          (Roll, like dice - combinations )
    /deal <n>  - show n faces, no repeats.  (Deal like cards - permutations )
    """

    def func(self):
        """ """
        cmd = self.cmdstring
        opt = self.switches
        # args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        char = self.character
        where = self.obj  # Where the dice rolling action is. (On the dice object)
        here = char.location  # Where the roller is.
        # outside = where.location  # If you happen to be inside the dice, this is outside.
        player = self.player
        my_die = char.db.dice  # Check if character has any dice sets stored on it.
        #  Does Die Exist?
        if not my_die:  # Inform player how to add. Also suggest using help.
            player.msg('You have no custom die yet. Use |y%s|g/new |w<|cdie name|w>|n to add a die.|/'
                       'See: |ghelp mydie|n for more information' % cmd)
            return
        else:
            current = 'My First Die'  # Where will selected die be stored? Recall from state storage here. TODO
            # Is this Usage of Die or Modification of Die?
            if not rhs:  # If no = sign given, then using, not modifying.
                # If using, randomize the die and store the result.
                char.ndb.roll_result = random.shuffle(my_die)  # Stored on character.
                # Usage check for appropriate switches (ignore incorrect ones typos/new/add/rem <show)
                # Generate roll result
                result = []  # Start with an empty list.
                if 'multi' in opt:
                    pass  # TODO - get n results and append into result list.
                if 'deal' in opt:
                    pass  # TODO - draw n results from faces.
                    #  (assuming n not > face_count, else repeats from next deck), append result.
                else:  # A single roll.
                    result = char.ndb.roll_result[0]
                if 'list' in opt or 'show' in opt or 'shuffle' in opt:  # Shows all the die faces (Only to player?)
                    face_count = len(char.ndb.roll_result)
                    faces = '|c' + '|w, |c'.join(my_die if 'shuffle' in opt else char.db.dice)  # Potentially shuffle.
                    player.msg('The current die, %s, has |g%i|n sides marked %s' % (current, face_count, faces))
                # Next, send result to appropriate parties per options.
                if 'hidden' in opt:  # Pose that character rolled current die, but do not display result.
                    here.msg_contents('%s%s|n rolls a hidden %s die.' % (char.STYLE, char.key, current))
                elif 'secret' in opt:  # Only give results to the character.
                    char.msg('You rolled %s to get %s.' % (current, result))
                else:  # Pose roll and results.
                    here.msg_contents('%s%s|n rolls the %s die from the %s%s|n to get %s' %
                                      (char.STYLE, char.key, current, where.STYLE, where.key, result))
            else:  # Modifying die
                # Use switches to determine what to do, check for conflict no add & rem
                # Inform use they have create die name they now need to /add faces
                pass  # TODO - Need to design structure of dictionary before modifying.
