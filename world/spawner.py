# -*- coding: utf-8 -*-
#from evennia.utils import spawner
from evennia.prototypes import spawner
from typeclasses.objects import Junk


def _batch_create_object(*objparams):
    """
    This is a cut-down version of the create_object() function,
    optimized for speed. It does NOT check and convert various input
    so make sure the spawned Typeclass works before using this!

    Args:
        objsparams (tuple): Parameters for the respective creation/add
            handlers in the following order:
                - `create_kwargs` (dict): For use as new_obj = `ObjectDB(**create_kwargs)`.
                - `permissions` (str): Permission string used with `new_obj.batch_add(permission)`.
                - `lockstring` (str): Lockstring used with `new_obj.locks.add(lockstring)`.
                - `aliases` (list): A list of alias strings for
                    adding with `new_object.aliases.batch_add(*aliases)`.
                - `nattributes` (list): list of tuples `(key, value)` to be loop-added to
                    add with `new_obj.nattributes.add(*tuple)`.
                - `attributes` (list): list of tuples `(key, value[,category[,lockstring]])` for
                    adding with `new_obj.attributes.batch_add(*attributes)`.
                - `tags` (list): list of tuples `(key, category)` for adding
                    with `new_obj.tags.batch_add(*tags)`.
                - `execs` (list): Code strings to execute together with the creation
                    of each object. They will be executed with `evennia` and `obj`
                        (the newly created object) available in the namespace. Execution
                        will happend after all other properties have been assigned and
                        is intended for calling custom handlers etc.
            for the respective creation/add handlers in the following
            order: (create_kwargs, permissions, locks, aliases, nattributes,
            attributes, tags, execs)

    Returns:
        objects (list): A list of created objects

    Notes:
        The `exec` list will execute arbitrary python code so don't allow this to be available to
        unprivileged users!

    """

    # Spawn in bulk: 1 or more objects

    # pool = [each for each in evennia.search_tag('pool') if not each.location]
    pool = [each for each in Junk.objects.all()]  # All junk objects in a list
    # (each for each in Junk.objects.all()) returns a generator object
    # Junk.objects.all() returns a Query set
    print('Number of objects to spawn: %i' % len(objparams))
    recycle = False
    if len(objparams) <= len(pool):
        dbobjs = pool[0:len(objparams)]
        recycle = True
        print('Re-using objects: ' + repr(dbobjs))
    else:
        dbobjs = [ObjectDB(**objparam[0]) for objparam in objparams]
        print('Creating fresh objects: ' + repr(dbobjs))
    objs = []
    for iobj, obj in enumerate(dbobjs):
        # call all setup hooks on each object
        objparam = objparams[iobj]
        print('Using parameters: ' + repr(objparam[0]))
        # Modify reused objects by replacing
        # 'db_destination', 'db_typeclass_path', 'db_location'
        # 'db_key', 'db_home'.
        if recycle:
            if obj.key != objparam[0]['db_key']:
                print(repr(obj.key) + ' => ' + repr(objparam[0]['db_key']))
                obj.key = objparam[0]['db_key']
            if obj.location != objparam[0]['db_location']:
                obj.location = objparam[0]['db_location']
                print(repr(obj.key) + ' =moving to> ' + repr(obj.location))
            if obj.destination != objparam[0]['db_destination']:
                obj.destination = objparam[0]['db_destination']
            print(repr(obj.typeclass_path) + ' => ' + repr(objparam[0]['db_typeclass_path']))
            obj.swap_typeclass(objparam[0]['db_typeclass_path'],
                               clean_attributes=True, clean_cmdsets=True)
            if obj.home != objparam[0]['db_home']:
                obj.home = objparam[0]['db_home']
            # TODO: Remove aliases, permissions, locks

            obj.aliases.clear()
            obj.clear_contents()
            obj.clear_exits()

        obj._createdict = {"permissions": make_iter(objparam[1]),
                           "locks": objparam[2],
                           "aliases": make_iter(objparam[3]),
                           "nattributes": objparam[4],
                           "attributes": objparam[5],
                           "tags": make_iter(objparam[6])}
        # this triggers all hooks
        obj.save()
        # run eventual extra code
        for code in objparam[7]:
            if code:
                exec(code, {}, {"evennia": evennia, "obj": obj})
        objs.append(obj)
    print('Spawning objects: ' + repr(objs))
    return objs
