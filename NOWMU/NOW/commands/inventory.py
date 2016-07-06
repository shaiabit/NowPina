from evennia import default_cmds
from evennia.utils import evtable
from world.helpers import mass_unit


class CmdInventory(default_cmds.MuxCommand):
    """
    Shows your inventory: carrying, wielding, wearing, obscuring.
    Usage:
      inventory
    Switches:
    /weight   shows inventory item weight and carry total
    """
    key = 'inventory'
    aliases = ['inv', 'i']
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'

    def func(self):
        """check inventory"""
        you = self.caller
        items = you.contents
        if not items:
            string = 'You are not carrying anything.'
        else:
            table = evtable.EvTable(border='header')
            for item in items:
                imass = mass_unit(item.get_mass()) if hasattr(item, 'get_mass') else '- unknown -'
                second = '(|y%s|n) ' % imass if 'weight' in self.switches else ''
                second += item.db.desc_brief or item.db.desc
                table.add_row('%s' % item.mxp_name(you.sessions, '@verb #%s' % item.id)
                              if hasattr(item, 'mxp_name')
                              else item.get_display_name(you.sessions), second and second or '')
            imass = you.get_mass() if hasattr(item, 'get_mass') else '- unknown -'
            string = "|wYou (%s) and what you carry (%s) total |y%s|n:\n%s" % (mass_unit(you.db.mass),
                                                                               mass_unit(imass - you.db.mass),
                                                                               mass_unit(imass), table)
        you.msg(string)