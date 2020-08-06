"""
Effects system
By: whitenoise, 6/5/2016
"""

from collections import OrderedDict
from datetime import datetime
from evennia import create_script
from operator import itemgetter
import uuid

# TODO: Make Effects for Characters and Rooms. Room Effects would change
# light, water level, etc.


class EffectException(Exception):
    """
    Base exception class raised by `Effect` objects.

    Args:
        msg (str): informative error message
    """
    def __init__(self, msg):
        self.msg = msg


class EffectHandler(object):
    """ EffectHandler will not only handle the addition and removal of Effects
    from an object, but it will also handle the processing of those Effects."""
    def __init__(self, obj, immediately_process=False, db_attribute='effects'):
        self.obj = obj
        self.immediately_process = immediately_process
        if not obj.attributes.has(db_attribute):
            obj.attributes.add(db_attribute, OrderedDict())
        self.effects = obj.attributes.get(db_attribute)

    def __len__(self):
        return len(self.effects)

    def __getattr__(self, effect):
        return self.get(effect)

    def __getitem__(self, effect):
        return self.get(effect)

    def get(self, eid):
        if eid not in self.effects:
            return None
        return self.effects[eid]

    def add(self, effect):
        key = effect.eid
        if key in self.effects:
            raise EffectException("Effect '{}' already exists.".format(key))

        # TODO: check if Effect has valid fields?

        self.effects[key] = effect

        if self.immediately_process:
            self.process(key)

    def remove(self, eid):
        if eid not in self.effects:
            raise EffectException("Effect not found: {}".format(eid))
        del self.effects[eid]

    def clear(self):
        for effect in self.all:
            self.remove(effect)

    @property
    def all(self):
        all_effects = []
        for effect in self.effects.itervalues():
            all_effects.append(effect)
        return all_effects

    def process(self, eid=None, target=None, effecthandler_attr='effects',
                traithandler_attr='traits'):
        """
        Processes the next effect in the queue.
        """
        # grab effect passed in or off the top
        if eid:
            effect = self.effects.pop(eid)
        else:
            if len(self.effects):
                effect = self.popitem()[1]
            else:
                return False

        if target is None:
            target = self.obj
        # fire!
        effect(target, effecthandler_attr, traithandler_attr)
        return True


class Effect(tuple):
    __slots__ = ()
    _fields = ('name', 'power', 'affectedTrait', 'duration',
               'delay', 'interval', 'script', 'time', 'eid')

    def __new__(cls, name, power, affectedTrait,
                duration=1, delay=0, interval=3, script=None,
                time=str(datetime.now()), eid=uuid.uuid1().hex):
        return tuple.__new__(cls, (name, power, affectedTrait, duration, delay,
                             interval, script, time, eid))

    def tick(self):
        return Effect(self.name, self.power, self.affectedTrait,
                      self.duration, self.delay-1, self.interval,
                      self.script, str(datetime.now()))

    def __call__(self, target, effecthandler_attr, traithandler_attr):
        traithandler = getattr(target, traithandler_attr)
        trait = traithandler.get(self.affectedTrait)
        if trait:
            # try to affect the trait by the power
            trait += self.power
            if self.duration:
                if self.script:
                    # create script
                    create_script(self.script,
                                  name="effect_%s_%s" % (self.name,
                                                         self.eid),
                                  interval=self.interval,
                                  start_delay=self.delay,
                                  repeats=self.duration,
                                  persistent=True,
                                  obj=target)
                    return
                else:
                    if (self.duration-1) > 1:
                        new_effect = self.tick()
                        effecthandler = getattr(target, effecthandler_attr)
                        effecthandler.add(new_effect)
        else:
            raise EffectException("No such Trait\
                                   '{}'".format(self.affectedTrait))

    def _asnamedtuple(self):
        return 'Effect(name=%r, power=%r, affectedTrait=%r, duration=%r,\
                delay=%r, interval=%r, script=%r, time=%r, eid=%r)' % self

    def _asdict(self):
        return OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        return tuple(self)

    __dict__ = property(_asdict)
    __namedtuple__ = property(_asnamedtuple)

    def __getstate__(self):
        pass

    name = property(itemgetter(0), doc='Name of the Effect')
    power = property(itemgetter(1), doc='Potency of the Effect')
    affectedTrait = property(itemgetter(2), doc='Trait affected by the Effect')
    duration = property(itemgetter(3), doc='How many times the Effect fires')
    delay = property(itemgetter(4), doc='How long until the Effect starts')
    script = property(itemgetter(5), doc='Script attached to Effect')
    time = property(itemgetter(6), doc='Timestamp for Effect')
    eid = property(itemgetter(7), doc='Unique ID for Effect')
