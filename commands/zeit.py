import datetime
import astral
import astral.sun
import astral.moon
from django.conf import settings
from django.utils import timezone
from commands.command import MuxCommand
from evennia.utils.evtable import EvTable
from evennia.utils import logger, utils, gametime, create


class CmdTime(MuxCommand):
    """
    show server time statistics
    Usage:
      time
    List Server time statistics such as uptime
    and the current time stamp.
    """
    key = 'time'
    aliases = 'uptime'
    locks = 'cmd:perm(time) or perm(denizen)'
    help_category = 'World'
    account_caller = True

    def func(self):
        """Show server time data in a table."""
        lat, lon, ele = 33.43, -112.07, 24
        here = self.character.location
        if here:
            x = float(here.tags.get(category="coordx", default=0))
            y = float(here.tags.get(category="coordy", default=0))
            # z = here.tags.get(category="coordz")
            if x and y:
                lat, lon = float(y/10000), float(x/10000)
                print('Using location coordinates: {}, {}'.format(lat, lon))

        place = astral.LocationInfo(timezone='UTC', latitude=lat, longitude=lon)
        obsr = astral.Observer(latitude=lat, longitude=lon, elevation=ele)


        def time_dif(at, when):
            diff = abs(at - when)
            return 'now' if diff.total_seconds() < 60 else (utils.time_format(diff.total_seconds(), 2) +
                                                          (' ago' if at > when else ''))

        def moon_phase(days):
            """
            Summarize the visible portion, given days into cycle
            Args:
                days (int or float): days into current cycle
            Returns:
                phase (str): summary of view of visible portion
            """
            phases = ('new', 'waxing crescent', 'First quarter', 'waxing gibbous',
                      'full', 'waning gibbous', 'last quarter', 'waning crescent')
            percent = float((float(days) + 0.5) / 29.53)
            phase = int((percent - int(percent)) * len(phases))
            return phases[phase]
        try:
            sun = astral.sun.sun(date=datetime.date.today(), observer=obsr)
        except Exception as e:
            return
        else:
            past = here.tags.get('past', category='realm')
            moon = astral.moon.phase(date=datetime.date.today())
            now = timezone.now()
            moment = ['dawn', 'sunrise', 'noon', 'sunset', 'dusk']
            events = zip([each.capitalize() + ':' for each in moment], [time_dif(now, sun[each]) for each in moment])
            table1 = EvTable("|wServer", '|wtime', align='l', width=75)
            table1.add_row('Current uptime', utils.time_format(gametime.uptime(), 3))
            table1.add_row('First start', time_dif(datetime.datetime.now(),
                                                   datetime.datetime.fromtimestamp(gametime.server_epoch())))
            if here.tags.get('past', category='realm'):
                table1.add_row('Moon phase', moon_phase(moon))
            table1.reformat_column(0, width=20)
            up = self.cmdstring == 'uptime'  # User asking for uptime mode
            self.msg(('Current uptime: ' + utils.time_format(gametime.uptime(), 3)) if up else str(table1))
            if past:  # Astral events are to be displayed while in past realm
                table2 = EvTable("|wEvent", "|wTime until", align="l", width=75)
                for entry in events:
                    table2.add_row(entry[0], entry[1])
                table2.reformat_column(0, width=20)
                self.msg(str(table2) if self.cmdstring == 'events' else ('\n' + str(table2)))
