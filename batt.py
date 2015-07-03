# -*- coding: utf8 -*-

import sys
import datetime
import calendar

from core.db import SensorsTable, sqla, db
from core.functions import get_time
from core.speak import speak

# Test...
db.execution_options(isolation_level="READ UNCOMMITTED")

def get_vbatt_time(date):
    is_vbatt = False
    last_vbatt_start = None
    total_vbatt = datetime.timedelta()

    c = SensorsTable.c
    query = sqla.select([ c.value, c.date ]) \
            .where(sqla.sql.func.substr(c.date, 1, 10)==date) \
            .where(c.name=='vsource') \
            .order_by(c.date.asc())
    for line in db.execute(query).fetchall():
        if not is_vbatt and line[0] == 'vbatt':
            is_vbatt = True
            #print('Vbatt start at %s' % (line[1]))
            last_vbatt_start = line[1]
        elif is_vbatt and line[0] == 'vin':
            is_vbatt = False
            total_vbatt += line[1] - last_vbatt_start
            #print('Vbatt stop at %s -> %s' % (line[1], total_vbatt))

    return total_vbatt

if __name__ == '__main__':

    def usage():
        print('''Usage :
- {name} 2015-06-11         Calculate and print use time for vbatt
- {name} 2015-06-11 tweet   Calculate, print and tweet use time for vbatt
- {name} yesterday tweet    Calculate, print and tweet use time for vbatt
        '''.format(name=sys.argv[0]))
        sys.exit()

    try:
        status = False
        if len(sys.argv) <= 1 or sys.argv[1] == 'help':
            usage()
        else:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') if sys.argv[1] == 'yesterday' else sys.argv[1]

            total_vbatt = get_vbatt_time(date)
            print(total_vbatt)

        if total_vbatt and sys.argv[len(sys.argv) - 1] == 'tweet':
            from config import secret, general as config
            from core import dialog

            message = speak(dialog.stats_vbatt_yesterday, total=get_time(total_vbatt.total_seconds()))

            if config.FAKE_MODE or not config.TWITTER_ON:
                print(message)
            else:
                from twython import Twython
                twt = Twython(secret.TWITTER_CONSUMER_KEY, secret.TWITTER_CONSUMER_SECRET, secret.TWITTER_OAUTH_TOKEN, secret.TWITTER_OAUTH_SECRET)
                twt.update_status(status=message)

    except Exception as e:
        print('Error while generating data (%s) !' % e)

