
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as dates

import datetime

from core.db import SensorsTable, sqla, db

#print(SensorsTable.c)

def get_data_from_days(day=None, pastdays=None, lastday=None):
    '''
    Get data from days
    - day : The date (ex: day=datetime.datetime.utcnow())
    - pastdays : If 0 : only current day, if 1, yesterday + today, etc...
    - lastday : If 0 : get the data from current day
    '''

    c = SensorsTable.c

    if day:
        #date1 = date2 = str(day)[:10]
        date1 = date2 = day
    elif lastday is not None:
        date = datetime.datetime.utcnow()
        #date1 = str(date - datetime.timedelta(days=lastday))[:10]
        date1 = date - datetime.timedelta(days=lastday)
        date2 = date1
    elif pastdays is not None:
        date = datetime.datetime.utcnow()
        #date1 = str(date - datetime.timedelta(days=pastdays))[:10]
        #date2 = str(date)[:10]
        date1 = date - datetime.timedelta(days=pastdays)
        date2 = date

    #date1 += ' 00:00:00'
    #date2 += ' 23:59:59'
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

        #print(date, date.strftime('%Y-%m-%d %H:%M:%S'))
        data[name].append(value)
        time[name].append(date)#.strftime('%Y-%m-%d %H:%M:%S'))

    return data, time

def generate_plot(data, time, informations, xlabel, ylabel):

    '''
    red_patch = mpatches.Patch(color='red', label='Enceinte')
    blue_patch = mpatches.Patch(color='blue', label='Nid 2')
    yellow_patch = mpatches.Patch(color='yellow', label='Luminosité')
    '''

    params = []
    patches = []
    labels = []
    fills = []
    for name, info in informations.items():
        desc, attributes = info
        if type(attributes) == str:
            color = attributes
            fill = False
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

    #print(data.keys())
    #plt.plot([1,2,3,4])
    #data['1w_1'].reverse()
    #plt.plot(data['temp'], 'r--', data['1w_2'], 'bs')
    #plt.plot(data['temp'], 'r', data['1w_2'], 'g', data['vbatt'], 'b', data['current'], 'y')

    '''
    plt.plot(*params)
    plt.gcf().autofmt_xdate()
    '''


    fig, ax = plt.subplots()
    ax.plot(*params)
    ax.xaxis.set_major_formatter(dates.DateFormatter('%d %b %H:%M'))
    fig.autofmt_xdate()

    #print(len(params))
    #print(informations)
    #ax.fill(params[12], params[13], 'orange', alpha=.5)

    # Fill...
    for fill in fills:
        ax.fill(fill[0], fill[1], fill[2], alpha=.5)

    fig.legend(handles=patches, loc=2, labels=labels)

    '''
    plt.plot(
        data['temp'], 'red', # Enceinte
        data['1w_2'], 'blue', # Nid 2
        data['lux'],  'yellow',

        #data['1w_1'], 'b', # Extérieur
        #data['1w_0'], 'b', # Nid 1
    )
    '''

    #plt.text(25, 10, r'$\mu=100,\ \sigma=15$')
    #plt.axis([0, 50, -5, 40])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    '''
    plt.annotate('Hop', xy=(25, 13), xytext=(30, 10),
                arrowprops=dict(facecolor='black', shrink=0.05),
                )
    '''

    plt.grid(True)
    #plt.show()
    plt.savefig('test.png')#, dpi=1)#, dpi=10) 

if __name__ == '__main__':

    #data, time = get_data_from_days(day=datetime.datetime.utcnow())
    data, time = get_data_from_days(pastdays=4)
    #data, time = get_data_from_days(lastday=1)

    from collections import OrderedDict
    i = OrderedDict()
    i['1w_0'] = ('Extérieur',  'violet')
    i['temp'] = ('Enceinte',   'red')
    i['1w_1'] = ('Nid 1',      'green')
    i['1w_2'] = ('Nid 2',      'blue')
    i['lux']  = ('Luminosité', ( 'orange', True ))

    generate_plot(data, time, i, 'Temps', 'Températures')

    '''
    import datetime
    import random
    import matplotlib.pyplot as plt

    # make up some data
    x = [datetime.datetime.now() + datetime.timedelta(hours=i) for i in range(12)]
    y = [i+random.gauss(0,1) for i,_ in enumerate(x)]

    print(x)
    print(y)

    # plot
    plt.plot(x,y)#, label='Super')#, 'r')
    # beautify the x-labels
    plt.gcf().autofmt_xdate()

    #plt.show()
    plt.savefig('test.png')#, dpi=1)#, dpi=10) 
    '''

