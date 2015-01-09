# -*- coding: utf8 -*-

import sys
import datetime
import calendar

from collections import OrderedDict

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as dates

from core.db import SensorsTable, sqla, db

EXPORT_FILE = '/tmp/plot.png'

info = OrderedDict()
info['1w_0'] = (u'Extérieur',  'violet')
info['temp'] = ('Enceinte',   'red')
info['1w_1'] = ('Nid 1',      'green')
info['1w_2'] = ('Nid 2',      'blue')
info['lux']  = (u'Luminosité', ( 'orange', True ))
info['pir'] = ('PIR',         'black')

def get_data_from_range(days=None):
    '''
    Get data from days
    - days :
      Get the data from the range, range is a tuple (x, y) with x
      is the old day and y the most recent day :
      ex:
        (0, 0)  : get only the current day
        (-1, 0) : get yesterday + current day
        (1, 1)  : get tomorrow
    '''

    def get_day(day):
        if type(day) is int:
            return (datetime.datetime.now() + datetime.timedelta(days=day)) \
                .replace(hour=0, minute=0, second=0, microsecond=0)
        elif type(day) is str:
            for item in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
                try:
                    return datetime.datetime.strptime(day, item)
                except ValueError:
                    pass
            raise Exception('Incorrect day type !')
        elif type(day) == datetime.datetime:
            return day
        else:
            raise Exception('Incorrect day type !')

    c = SensorsTable.c

    date1, date2 = get_day(days[0]), get_day(days[1])
    if str(date1) == date1.strftime('%Y-%m-%d 00:00:00') and str(date2) == date2.strftime('%Y-%m-%d 00:00:00'):
        date1 = date1.strftime('%Y-%m-%d 00:00:00')
        date2 = date2.strftime('%Y-%m-%d 23:59:59')

    query = sqla.select([c.name, c.value, c.date]).where(c.date>=date1).where(c.date<=date2)

    print(query, date1, date2)

    data = {}
    time = {}
    for line in db.execute(query):
        name, value, date = line

        try:
            data[name]
        except KeyError:
            data[name] = []

        try:
            time[name]
        except KeyError:
            time[name] = []

        data[name].append(value)
        time[name].append(date)

    return data, time

def generate_plot(data, time, informations, xlabel, ylabel, dateformat='%H:%M', exportfile=EXPORT_FILE):

    params = []
    patches = []
    labels = []
    fills = []
    for name, info in informations.items():
        desc, attributes = info
        if type(attributes) == str:
            color, fill = attributes, False
        else:
            color, fill = attributes

        patches.append(mpatches.Patch(color=color, label=desc))
        labels.append(desc)

        try:
            data[name]
        except KeyError:
            data[name] = []

        try:
            time[name]
        except KeyError:
            time[name] = []

        if fill:
            fills.append((time[name], data[name], color))

        params.append(time[name])
        params.append(data[name])
        params.append(color)

    fig, ax = plt.subplots()
    ax.plot(*params)
    #ax.xaxis.set_major_formatter(dates.DateFormatter('%d %b %H:%M'))
    ax.xaxis.set_major_formatter(dates.DateFormatter(dateformat))
    fig.autofmt_xdate()

    # Fill...
    for fill in fills:
        ax.fill(fill[0], fill[1], fill[2], alpha=.5)

    #fig.legend(handles=patches, loc=1, labels=labels)
    #fig.legend(handles=patches, labels=labels, loc='upper center', bbox_to_anchor=(0.5, 1.05),
    #      ncol=3, fancybox=True, shadow=True)

    lgd = fig.legend(handles=patches, labels=labels, loc='upper center', bbox_to_anchor=(0.5, .99),
          fancybox=True, shadow=True, ncol=3)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    '''
    plt.annotate('Hop', xy=(25, 13), xytext=(30, 10),
                arrowprops=dict(facecolor='black', shrink=0.05),
                )
    '''

    plt.grid(True)
    plt.savefig(exportfile, bbox_extra_artists=(lgd,))#, bbox_inches='tight')#, dpi=1)#, dpi=10)

    return True

def generate_plot_from_range(days, dateformat='%H:%M', exportfile=EXPORT_FILE):
    data, time = get_data_from_range(days)
    return generate_plot(data, time, info, u'Temps', u'Températures', dateformat=dateformat, exportfile=exportfile)

if __name__ == '__main__':

    def usage():
        print('''Usage :
- {name} today      Generate plot with current day data
- {name} yesterday  Generate plot with yesterday data
- {name} lastweek   Generate plot with last week data
- {name} lastmonth  Generate plot with last month data
- {name} range x y  Generate plot from range x to y (where x and y are in datetime format)
        '''.format(name=sys.argv[0]))
        sys.exit()

    try:
        status = False
        if len(sys.argv) <= 1 or sys.argv[1] == 'help':
            usage()
        elif sys.argv[1] == 'today':
            status = generate_plot_from_range((0, 0), dateformat='%H:%M')
        elif sys.argv[1] == 'yesterday':
            status = generate_plot_from_range((-1, -1), dateformat='%H:%M')
        elif sys.argv[1] == 'lastweek':
            status = generate_plot_from_range((-7, -1), dateformat='%d %b %H:%M')
        elif sys.argv[1] == 'lastmonth':

            lastmonth = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
            start = lastmonth.replace(day=1)

            #year, month = [ int(data) for data in lastmonth.strftime('%Y,%m').split(',') ]
            year, month = map(lambda a: int(a), lastmonth.strftime('%Y,%m').split(','))
            _, daycount = calendar.monthrange(year, month)

            end = start + datetime.timedelta(days=daycount - 1)

            status = generate_plot_from_range((start, end), dateformat='%d %b %H:%M')
        elif sys.argv[1] == 'range':
            status = generate_plot_from_range((sys.argv[2], sys.argv[3]), dateformat='%d %b %H:%M')
        else:
            usage()

        if sys.argv[len(sys.argv) - 1] == 'tweet' and status:
            from config import secret, general as config
            from core import dialog
            from twython import Twython

            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            week = (datetime.datetime.now() - datetime.timedelta(weeks=1)).strftime('%W, %Y')
            month = (datetime.datetime.now() - datetime.timedelta(weeks=1)).strftime('%Y-%m')

            message = {
                'yesterday':    dialog.stats_yesterday % yesterday,
                'lastweek':     dialog.stats_lastweek % week,
                'lastmonth':    dialog.stats_lastmonth % month
            }[sys.argv[1]]

            if config.FAKE_MODE or not config.TWITTER_ON:
                print(message)
            else:
                twt = Twython(secret.TWITTER_CONSUMER_KEY, secret.TWITTER_CONSUMER_SECRET, secret.TWITTER_OAUTH_TOKEN, secret.TWITTER_OAUTH_SECRET)
                twt.update_status_with_media(status=message, media=open(EXPORT_FILE, 'r'))

    except Exception as e:
        print('Error while generating data (%s) !' % e)

