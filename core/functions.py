# -*- coding: utf8 -*-

import random
import glob
import time

def speak(data):
    '''
    Speak random text
    '''
    out = []
    for i in xrange(1, len(data)):
        items = []
        for weight, value in data[i]:
            for w in xrange(weight):
                items.append(value)

        random.shuffle(items)
        out.append(items[0])

    return data[0].format(*out)

def elapsed_time(seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
    """
    Takes an amount of seconds and turns it into a human-readable amount of time.
    """
    # the formatted time string to be returned
    time = []
     
    # the pieces of time to iterate over (days, hours, minutes, etc)
    # - the first piece in each tuple is the suffix (d, h, w)
    # - the second piece is the length in seconds (a day is 60s * 60m * 24h)
    parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
        (suffixes[1], 60 * 60 * 24 * 7),
        (suffixes[2], 60 * 60 * 24),
        (suffixes[3], 60 * 60),
        (suffixes[4], 60),
        (suffixes[5], 1)]
     
    # for each time piece, grab the value and remaining seconds, and add it to
    # the time string
    for suffix, length in parts:
        value = int(seconds / length)
        if value > 0:
            seconds = seconds % length
            time.append('%s %s' % (str(value),
                (suffix, (suffix, suffix + 's')[value > 1])[add_s]))
        if seconds < 1:
            break
     
    return separator.join(time)

def get_time(seconds):
    return elapsed_time(seconds, ['année', 'semaine', 'jour', 'heure', 'minute', 'seconde'], add_s=True)

class FifoBuffer:
    
    size = -1
    default = None

    def __init__(self, data=default, size=-1):
        if data:
            self.size = len(data)
            self.data = data
        else:
            self.size = size
            self.data = [ self.default ] * size

    def isFull(self):
        for val in self.data:
            if val == self.default:
                return False
        return True

    def append(self, x):
        self.data.pop(0)
        self.data.append(x)

    def get(self):
        return self.data

def onewire_read_temperature(sensors, fahrenheit=False, maxretry=3, basedir='/sys/bus/w1/devices/'):
    '''
    Read temperature from 1Wire bus
    Todo:
     * Read 2 times and compares output
    '''

    device_folders = glob.glob(basedir + '??-*')

    def parse(data):
        while not data or data[0].strip()[-3:] != 'YES':
            return (False, 0)

        equals_pos = data[1].find('t=')
        if equals_pos != -1:
            temp_string = data[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return (True, temp_c if not fahrenheit else temp_c * 9.0 / 5.0 + 32.0)

    def get_device_path(key):
        if type(key) == int:
            return device_folders[key]
        elif type(key) == str:
            for path in device_folders:
                if path[-len(key):] == key:
                    return path

    out = []
    for sensor in sensors if type(sensors) == list else [ sensors ]:

        path = get_device_path(sensor)

        if not path:
            continue

        retry = 0
        while True:
            lines = None
            try:
                with open(path + '/w1_slave', 'r') as file:
                    lines = file.readlines()
            except (IndexError, IOError):
                out.append(None)
                break

            status, data = parse(lines)
            if status:
                out.append(data)
                break

            if retry == maxretry:
                out.append(None)
                break

            time.sleep(0.2)

            retry += 1

    if type(sensors) == str:
        if not len(out):
            return None
        else:
            return out[0]
    else:
        return out
    #return None if type(sensors) == str else out if not len(out) or type(sensors) == list else out[0]

def only_one_call_each(seconds=None, minuts=None, hours=None, days=None, withposarg=None):
    '''
    Decorator function : limit function call
    Todo:
    - Handle keyword arg (withkeyarg)
    - Handle multiple args
    '''

    _seconds = 0
    for var, delay in ( ('seconds', 1), ('minuts', 60), ('hours', 60 * 60), ('days', 60 * 60 * 24) ):
        if locals()[var] is not None:
            _seconds += locals()[var] * delay

    def decorator(func):
        last = {}
        def wrapper(*args, **kwargs):
            #nonlocal last
            arg = args[withposarg] if withposarg is not None else None
            if arg in last and last[arg] and last[arg] + _seconds > time.time():
                return

            func(*args, **kwargs)
            last[arg] = time.time()
        return wrapper

    return decorator

if __name__ == '__main__':
    result = onewire_read_temperature([0, 1, 2], basedir='/tmp/')
    print(result)

    result = onewire_read_temperature(['10-0008008ba2a9', '28-0000061496ff', '10-0008008bceb5'], basedir='/tmp/')
    print(result)

    result = onewire_read_temperature('28-0000061496ff', basedir='/tmp/')
    print(result)

