
import random
import glob
import time

from config.general import FAKE_MODE
if FAKE_MODE:
    #from fake import i2c
    from fake import adc
else:
    #import quick2wire.i2c as i2c
    from lib import adc

from lib.raspiomix import Raspiomix

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

def read_w1_temperature(index, fahrenheit=False, maxretry=3, basedir='/sys/bus/w1/devices/'):
    '''
    Read temperature from 1Wire bus
    Todo:
     * Read 2 times and compares output
     * Index arg as sensor id array (ex: index = [ '10-xxxxx', '28-XXXXxx' ])
    '''

    device_folder = glob.glob(basedir + '??-*')

    def parse(data):
        while not data or data[0].strip()[-3:] != 'YES':
            return (False, 0)

        equals_pos = data[1].find('t=')
        if equals_pos != -1:
            temp_string = data[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return (True, temp_c if not fahrenheit else temp_c * 9.0 / 5.0 + 32.0)

    out = []
    for item in index if type(index) == list else [ index ]:

        retry = 0
        while True:
            lines = None
            try:
                with open(device_folder[item] + '/w1_slave', 'r') as file:
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

    return out if not len(out) or type(index) == list else out[0]

def read_analog():
    '''
    Read analog value
    ''' 
    a = adc.adc()
    return a.getVoltages()

    '''
    varDivisior = 64 # from pdf sheet on adc addresses and config
    varMultiplier = (3.3/varDivisior)/1000
    varMultiplier = 0.0000386

    channels = [ 0, 0, 0, 0 ]

    with i2c.I2CMaster() as bus:
        def changechannel(address, adcConfig):
            bus.transaction(i2c.writing_bytes(address, adcConfig))

        def getadcreading(address):
            h, m, l ,s = bus.transaction(i2c.reading(address,4))[0]
            while (s & 128):
                h, m, l, s = bus.transaction(i2c.reading(address,4))[0]
            # shift bits to product result
            t = ((h & 0b00000001) << 16) | (m << 8) | l
            # check if positive or negative number and invert if needed
            if (h > 128):
                t = ~(0x020000 - t)
            return t * varMultiplier

        changechannel(Raspiomix.I2C_ADC_ADDRESS, 0x9C)
        channels[0] = round(getadcreading(Raspiomix.I2C_ADC_ADDRESS), 2)

        changechannel(Raspiomix.I2C_ADC_ADDRESS, 0xBC)
        channels[1] = round(getadcreading(Raspiomix.I2C_ADC_ADDRESS), 2)

        changechannel(Raspiomix.I2C_ADC_ADDRESS, 0xDC)
        channels[2] = round(getadcreading(Raspiomix.I2C_ADC_ADDRESS), 2)

        changechannel(Raspiomix.I2C_ADC_ADDRESS, 0xFC)
        channels[3] = round(getadcreading(Raspiomix.I2C_ADC_ADDRESS), 2)

        return channels
    '''

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

