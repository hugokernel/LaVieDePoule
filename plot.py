
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import datetime

from core.db import SensorsTable, sqla, db

#print(SensorsTable.c)

def get_data_from_days(day=None, pastdays=None):
    '''
    Get data from days
    - day : The date (ex: day=datetime.datetime.utcnow())
    - pastdays : If 0 : current day, if 1, yesterday + today, etc...
    '''

    c = SensorsTable.c

    if day:
        #date = str(datetime.datetime.utcnow())[:10]
        date1 = date2 = str(day)[:10]
    elif pastdays is not None:
        date = datetime.datetime.utcnow()
        date1 = str(date - datetime.timedelta(days=pastdays))[:10]
        date2 = str(date)[:10]

    date1 += ' 00:00:00'
    date2 += ' 23:59:59'

    query = sqla.select([c.name, c.value]).where(c.date>=date1).where(c.date<=date2)

    print(query, date1, date2)

    data = {}
    for line in db.execute(query):
        name, value = line

        try:
            data[name]
        except KeyError:
            data[name] = []

        data[name].append(value)

    return data

def generate_plot(data, informations):

    '''
    red_patch = mpatches.Patch(color='red', label='Enceinte')
    blue_patch = mpatches.Patch(color='blue', label='Nid 2')
    yellow_patch = mpatches.Patch(color='yellow', label='Luminosité')
    '''

    params = []
    patches = []
    for name, info in informations.items():
        desc, color = info
        patches.append(mpatches.Patch(color=color, label=desc))

        try:
            data[name]
        except KeyError:
            data[name] = []

        params.append(data[name])
        params.append(color)

    plt.legend(handles=patches, loc=3)

    #print(data.keys())
    #plt.plot([1,2,3,4])
    #data['1w_1'].reverse()
    #plt.plot(data['temp'], 'r--', data['1w_2'], 'bs')
    #plt.plot(data['temp'], 'r', data['1w_2'], 'g', data['vbatt'], 'b', data['current'], 'y')

    plt.plot(*params)

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
    plt.ylabel('Temperatures')
    plt.xlabel('Temps')

    '''
    plt.annotate('Hop', xy=(25, 13), xytext=(30, 10),
                arrowprops=dict(facecolor='black', shrink=0.05),
                )
    '''

    plt.grid(True)
    #plt.show()
    plt.savefig('test.png')#, dpi=1)#, dpi=10) 

if __name__ == '__main__':
    #data = get_data_from_days(day=datetime.datetime.utcnow())
    data = get_data_from_days(pastdays=0)

    from collections import OrderedDict
    i = OrderedDict()
    i['1w_1'] = ('Extérieur',  'green' )
    i['temp'] = ('Enceinte',   'red' )
    i['1w_0'] = ('Nid 1',      'violet' )
    i['1w_2'] = ('Nid 2',      'blue' )
    i['lux']  = ('Luminosité', 'yellow' )

    generate_plot(data, i)

