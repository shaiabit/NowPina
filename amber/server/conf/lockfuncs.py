# -*- coding: utf-8 -*-
from random import *

"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""


def tellfalse(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with tellfalse().
    A simple logger that always returns false. Prints to stdout
    for simplicity, should use utils.logger for real operation.
    """
    print("%s tried to access %s. Access denied.", accessing_obj, accessed_obj)
    return False


def half(accessing_obj, accessed_obj, *args, **kwargs):
    return False if random() > 0.5 else True


def on_path(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with on_path() and returns False
    when accessing_obj is on a path (inside an exit).
    """
    if not accessing_obj.location:
        return True  # Nowhere is not on a path.
    return True if accessing_obj.location.destination else False


def on_exit(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with on_exit() and returns True
    only when accessing_obj is on an exit within the room.
    Return True if char's loc contains a key of the same
    name as arg[0]
    """
    if not accessing_obj.location:
        return False  # Nowhere won't have exits
    coord = accessing_obj.ndb.grid_loc
    flag = accessing_obj.location.point(coord, args[0])
    return True if flag else False


def self(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with self() and returns True
    when accessing_obj is also the accessed_obj
    """
    return accessing_obj == accessed_obj


def rp(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with rp() and returns True
    when accessing_obj is in an room designated for
    rollplay and object has sdesc set.
    """
    return accessing_obj.attributes.has('_sdesc') and accessing_obj.location\
           and accessing_obj.location.tags.get('rp', category='flags')


def no_back(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with no_back() and returns True
    when accessing_obj unable to go back. (May be a trap!)
    """
    return False


def no_home(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with no_home() and returns False
    when accessing_obj unable to go home. (May already be home)
    """
    return True if not accessing_obj.home else False


def at_home(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with no_home() and returns False
    when accessing_obj unable to go home. (May already be home)
    """
    return True if accessing_obj.location == accessing_obj.home else False


def roll(accessing_obj, accessed_obj, *args, **kwargs):
    return True if args else False
