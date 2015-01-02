# -*- coding: utf8 -*-

"""
.____         ____   ___.__       ________        __________            .__
|    |   _____\   \ /   |__| ____ \______ \   ____\______   \____  __ __|  |   ____
|    |   \__  \\   Y   /|  _/ __ \ |    |  \_/ __ \|     ___/  _ \|  |  |  | _/ __ \
|    |___ / __ \\     / |  \  ___/ |    `   \  ___/|    |  (  <_> |  |  |  |_\  ___/
|_______ (____  /\___/  |__|\___  /_______  /\___  |____|   \____/|____/|____/\___  >
        \/    \/                \/        \/     \/                               \/"""

from __future__ import print_function
import sys
import time
import arrow
import logging
import curses
from fractions import Fraction
import threading
from datetime import datetime

try:
    reload
except NameError:
    from importlib import reload

from lib.kbhit import KBHit
from lib.RainbowHandler import RainbowLoggingHandler
from lib.freesms import send_sms

from core.db import TwitterActivityTable, EventsTable, SensorsTable, sqla, db
from core.functions import FifoBuffer, only_one_call_each
from core.sensors import Sensors
from core.speak import speak
from core import dialog

from config import general as config, secret

if config.FAKE_MODE:
    from core.fake import (  PiCamera, GPIO,
                            Twython, TwythonError, TwythonRateLimitError,
                            onewire_read_temperature, Raspiomix as Raspiomix_Origin,
                            Camera )
else:
    from lib.raspiomix import Raspiomix as Raspiomix_Origin
    from core.camera import Camera
    from twython import Twython, TwythonError, TwythonRateLimitError
    from picamera import PiCamera
    import RPi.GPIO as GPIO
    from core.functions import onewire_read_temperature

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

rainbowHandler = RainbowLoggingHandler(sys.stdout)
rainbowHandler.setFormatter(formatter)
logger.addHandler(rainbowHandler)

fileHandler = logging.FileHandler('laviedepoule.log')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

logger.setLevel(logging.DEBUG)

'''
Configure GPIO
'''
class Raspiomix(Raspiomix_Origin):
    IO4 = 7
    IO5 = 16

GPIOS = [
    Raspiomix.IO0,
    Raspiomix.IO1,
    Raspiomix.IO2,
    Raspiomix.IO3,
]

SWITCH0 = Raspiomix.IO0
SWITCH1 = Raspiomix.IO1
SWITCH2 = Raspiomix.IO3

PIR = Raspiomix.IO2

RELAY = Raspiomix.IO4
LED = Raspiomix.IO5

raspi = Raspiomix()

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

for index in GPIOS:
    GPIO.setup(index, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(PIR, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(LED, GPIO.OUT)
GPIO.setup(RELAY, GPIO.OUT)

IR_ON = lambda: GPIO.output(RELAY, False)
IR_OFF = lambda: GPIO.output(RELAY, True)
IR_OFF()

class PirActivity():

    # Interval in second
    interval = 30.0

    activities = []
    startat = False

    def __init__(self):
        self.startat = time.time()

    def add(self):
        print('pir!')
        self.clean()
        self.activities.append(time.time()) 

    def clean(self):
        now = time.time()
        new = []
        for activity in self.activities:
            if activity + self.interval < now:
                continue
            new.append(activity)
        self.activities = new

    def isReady(self):
        '''
        Ensure that interval is expired
        '''
        return self.startat + self.interval < time.time()

    def get(self):
        return len(self.activities)

'''
a = 0
while True:
    try:
        time.sleep(0.5)
        pira.add()
        a += 1
    except KeyboardInterrupt:
        import sys
        print(pira.get())
        sys.exit()
'''

pira = PirActivity()

sensor = Sensors(1 if config.FAKE_MODE else 10)

def get_maxima(name):
    c = SensorsTable.c
    query = sqla.select([c.name, sqla.sql.func.min(sqla.cast(c.value, sqla.Float)), \
        sqla.sql.func.max(sqla.cast(c.value, sqla.Float)), c.type ]).group_by(c.type, c.name). \
        where(c.name==name)
    name, _min, _max, type = db.execute(query).fetchone()
    return (_min, _max)

class Maxmin:

    sensor_name = '1w_0'

    minima_detected = None
    maxima_detected = None

    @staticmethod
    @sensor.detect_change(name=sensor_name)
    def detect_increase(name, value):
        if Maxmin.minima_detected is not None:
            _min, _ = get_maxima(name)
            twit(dialog.record_out_temp_min % (_min, Maxmin.minima_detected.humanize(locale='fr')))
            Maxmin.minima_detected = None

    @staticmethod
    @sensor.detect_change(name=sensor_name, unit_per_minut=-0.01)
    def detect_decrease(name, value):
        if Maxmin.maxima_detected is not None:
            _, _max = get_maxima(name)
            twit(dialog.record_out_temp_max % (_max, Maxmin.maxima_detected.humanize(locale='fr')))
            Maxmin.maxima_detected = None

    @staticmethod
    @sensor.set_threshold_callback(get_maxima, sensor_name)
    def detect_maxima(name, value, threshold):
        _min, _max = threshold
        if value < _min:
            Maxmin.minima_detected = arrow.utcnow()
        elif value > _max:
            Maxmin.maxima_detected = arrow.utcnow()

@sensor.set_ready()
@only_one_call_each(seconds=config.SAVE_TO_DB_EVERY, withposarg=0)
def save_to_db(name, value, last_save={}):
    _, _, _, type = sensor.sensors[name]
    db.execute(SensorsTable.insert().values(
        type=type,
        name=name,
        value=value,
        date=datetime.now(),
    ))

@sensor.set_not_in_range()
def notinrange(name, value, validrange):
    logger.error("%s sensor not in valid range (%d, range: %s) !" % (name, value, validrange))

@sensor.detect_change(name='1w_1', unit_per_minut=0.1, measure_count=5)
@sensor.detect_change(name='1w_2', unit_per_minut=0.1, measure_count=5)
def detect_increase(name, value):
    print('Increase detected !', name)

@sensor.detect_change(name='1w_1', unit_per_minut=-0.1, measure_count=5)
@sensor.detect_change(name='1w_2', unit_per_minut=-0.1, measure_count=5)
def detect_decrease(name, value):
    print('Decrease detected !', name)

@sensor.set_threshold_callback(config.TEMP_ALERT,    'temp')
@sensor.set_threshold_callback(config.VOLTAGE_ALERT, 'vbatt')
@sensor.set_threshold_callback(config.CURRENT_ALERT, 'current')
@only_one_call_each(hours=12, withposarg=0)
def alerts(name, value, validrange):

    messages = {
        'vbatt':    'Vbatt voltage (%0.2fV) not in range (thresholds: %s) !',
        'current':  'Current (%0.2fA) not in range (thresholds: %s) !',
        'temp':     'Main temperature (%i°C) not in range (thresholds: %s) !'
    }

    message = messages[name] % (value, validrange)

    if config.FAKE_MODE:
        logger.info(message)
    else:
        if config.TWITTER_ON:
            twit(('@%s ' % config.TWITTER_ADMIN_ACCOUNT) + message)
        send_sms(secret.FREESMS_LOGIN, secret.FREESMS_KEY, 'Poulailler: ' + message)


sensor.declare('vbatt',      lambda: raspi.readAdc(0) / 0.354,    type=sensor.TYPE_VOLTAGE)
sensor.declare('current',    lambda: raspi.readAdc(3) * 10 / 6.8, type='current')
sensor.declare('lux',        lambda: raspi.readAdc(1),            type='luminosity')

with sensor.attributes(type='switch'):
    sensor.declare('door0',      lambda: GPIO.input(SWITCH0))
    sensor.declare('door1',      lambda: GPIO.input(SWITCH1))
    sensor.declare('door2',      lambda: GPIO.input(SWITCH2))

with sensor.attributes(validrange=(-20, 50), type=sensor.TYPE_TEMPERATURE):
    sensor.declare('temp',   lambda: raspi.readAdc(2) * 100) # Enceinte
    sensor.declare('1w_0',   onewire_read_temperature, (config.ONEWIRE_SENSOR0,)) # Extérieur
    sensor.declare('1w_1',   onewire_read_temperature, (config.ONEWIRE_SENSOR1,)) # Nid 1
    sensor.declare('1w_2',   onewire_read_temperature, (config.ONEWIRE_SENSOR2,)) # Nid 2

sensor.declare('pir',   pira.get, type='activity')

#sensor.setNotInRangeCallback(lambda name, value, validrange: logger.error("%s sensor not in valid range (%d, range: %s) !" % (name, value, validrange)))
#sensor.setReadyCallback(save_to_db)

#sensor.setReadyCallback(detect_increase, '1w_1')

'''
for i in range(0, 20):
    detect_increase(i)

for i in range(0, 20):
    detect_increase(i)
'''

"""
while True:
    print(sensor.getLastValue())
    time.sleep(1)

i = 0
while True:
    #print(sensor.get('toto'))
    #print(sensor.getLastValue('1w_0', maxage))

    #print(sensor.getLastValue('1w_0', maxage=3, withtimestamp=True))
    #print(sensor.getLastValue(('1w_0', '1w_1', '1w_2'), maxage=3))
    #print(sensor.getLastValue(maxage=3))

    if i > 3:
        #vbatt, lux, temp, current = analog[0] / 0.354, analog[1], analog[2] * 100, analog[3] * 10 / 6.8
        #temp1, temp2, temp3 = onewire_read_temperature(config.ONEWIRE_SENSORS)

        values = sensor.getLastValue(('vbatt', 'lux', 'temp', 'current'), maxage=config.MAX_AGE)
        vbatt, lux, temp = values['vbatt'], values['lux'], values['temp']
        print(vbatt, lux, temp)

    '''
    if i > 5:
        val = sensor.getLastValue('1w_0', maxage=2)
        print('Value:', val, ', timestamp: ', time.time())

        vals = sensor.getLastValue(maxage=2)
        print(vals)
    '''

    time.sleep(0.5)
    i += 1
"""

class Twitter(threading.Thread):

    sources = []
    twitter = None

    def __init__(self, twitter):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

        self.twitter = twitter

        # Load all response
        s = sqla.select([TwitterActivityTable.c.source_id])
        for id, in db.execute(s):
            self.sources.append(id)

    def stop(self):
        self._stopevent.set()

    def run(self):

        def str2dtime(date):
            return datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')

        while not self._stopevent.isSet():

            #rates = self.twitter.get_application_rate_limit_status()
            #print(rates)
            #time.sleep(10)
            #continue

            mentions = self.twitter.get_mentions_timeline()
            for mention in mentions:

                if int(mention['id_str']) not in self.sources:

                    # Answer only mention contains 'cot'
                    if 'cot' not in mention['text'].lower():
                        continue

                    message = speak(dialog.cot, username=mention['user']['screen_name'])

                    logger.info('New twitter mention from %s, reponse: %s' % (mention['user']['screen_name'], message))

                    try:
                        response = self.twitter.update_status(status=message, in_reply_to_status_id=mention['id_str'])        

                        ins = TwitterActivityTable.insert().values(
                            source_id=mention['id_str'],
                            source_reply_id=mention['in_reply_to_status_id'],
                            source_user_name=mention['user']['screen_name'],
                            source_content=mention['text'],
                            source_date=str2dtime(mention['created_at']),
                            reply_id=response['id_str'],
                            reply_content=response['text'],
                            reply_date=str2dtime(response['created_at']),
                        )

                        db.execute(ins)

                        self.sources.append(int(mention['id_str']))

                    except (TwythonError, TwythonRateLimitError) as e:
                        logger.error(e)

            time.sleep(60 * 2)

'''
# Get your "home" timeline
twt.statuses.home_timeline()

# Get a particular friend's timeline
twt.statuses.user_timeline(screen_name="billybob")

# to pass in GET/POST parameters, such as `count`
twt.statuses.home_timeline(count=5)

# to pass in the GET/POST parameter `id` you need to use `_id`
twt.statuses.oembed(_id=1234567890)

# Send a direct message
twt.direct_messages.new(
    user="billybob",
    text="I think yer swell!")
'''

def twit(message, takephoto=False, **kwargs):
    message = speak(message, **kwargs) if type(message) == tuple else message

    logger.info('Twit: %s' % message)

    if config.TWITTER_ON:
        try:
            if takephoto:
                if cam.takePhoto():
                    twt.update_status_with_media(status=message, media=open(cam.photo_file, 'r'))
            else:
                twt.update_status(status=message)
        except TwythonError as e:
            logger.error(e)

class Events:

    bouncetime = 10000
    events = {}
    pir_counter = 0
    min_delay = 60 * 60

    inputs = {
       SWITCH0: 'switch0',
       SWITCH1: 'switch1',
       SWITCH2: 'switch2',
       PIR:     'pir'
    }

    def __init__(self):
        GPIO.add_event_detect(SWITCH0, GPIO.BOTH, callback=self.wrapper, bouncetime=self.bouncetime)
        GPIO.add_event_detect(SWITCH1, GPIO.BOTH, callback=self.wrapper, bouncetime=self.bouncetime)
        GPIO.add_event_detect(SWITCH2, GPIO.BOTH, callback=self.wrapper, bouncetime=self.bouncetime)

        GPIO.add_event_detect(PIR, GPIO.FALLING, callback=self.pir)#, bouncetime=self.bouncetime)

    def bouncesleep(func):
        def wrapper(*args, **kwargs):
            time.sleep(Events.bouncetime / 1000)
            return func(*args, **kwargs)
        return wrapper

    def timer(func):
        def wrapper(self, channel):
            try:
                name, _ = func.__name__.split('_')
            except ValueError:
                name = func.__name__

            if func.__name__ in Events.events:
                last_call = time.clock() - Events.events[func.__name__]
            else:
                last_call = last_event = 0

            if name in Events.events:
                last_event = time.clock() - Events.events[name]
            else:
                last_call = last_event = 0

            Events.events[func.__name__] = time.clock()
            Events.events[name] = time.clock()

            return func(self, channel, (last_call, last_event))
        return wrapper

    def saveLog(self, channel):
        ins = EventsTable.insert().values(
            input=self.inputs[channel],
            type='rising' if GPIO.input(channel) else 'falling',
            date=datetime.now(),
        )

        db.execute(ins)

    def log(func):
        def wrapper(self, channel):
            self.saveLog(channel)
            return func(self, channel)
        return wrapper

    @log
    @bouncesleep
    @timer
    def door0_falling(self, channel, times):
        if times[0] > self.min_delay:
            twit(dialog.collect_egg, time_last=get_time(times[0]))
        else:
            twit(dialog.collect_egg_light)

    @log
    @bouncesleep
    @timer
    def door0_rising(self, channel, times):
        logger.debug("Collecteur oeuf ferme ! (%s)", get_time(times[1]))

        # Power off status led !
        GPIO.output(LED, False)

    @log
    @bouncesleep
    @timer
    def door1_falling(self, channel, times):
        if times[0] > self.min_delay:
            twit(dialog.enclosure_close, time=get_time(times[0]))
        else:
            twit(dialog.enclosure_close_light)

    @log
    @bouncesleep
    @timer
    def door1_rising(self, channel, times):
        twit(dialog.enclosure)

    @log
    @bouncesleep
    @timer
    def door2_falling(self, channel, times):
        if times[0] > self.min_delay:
            twit(dialog.garden_close, time=get_time(times[0]))
        else:
            twit(dialog.garden_close_light)

    @log
    @bouncesleep
    @timer
    def door2_rising(self, channel, times):
        twit(dialog.garden_full)

    #@bouncesleep
    @timer
    def pir(self, channel, times):
        pira.add()

        '''
        self.pir_counter += 1 if times[0] < 1 else -self.pir_counter
        print('Pir !', times, self.pir_counter)
        if self.pir_counter == 2:
            self.saveLog(channel)
            logger.debug("Pir event detected !")
            self.pir_counter = 0
        '''

    def wrapper(self, channel):

        # Another debouncer...
        count = 0
        last_state = -1
        while True:
            state = GPIO.input(channel)
            count = count + 1 if last_state == state else 0
            if count >= 3:
                break
            last_state = state
            time.sleep(0.5)

        falling, rising = {
            SWITCH0:    (self.door0_falling, self.door0_rising),
            SWITCH1:    (self.door1_falling, self.door1_rising),
            SWITCH2:    (self.door2_falling, self.door2_rising),
        }[channel]

        logger.debug('Event wrapper ! Channel: %i (%s), state: %i' % (channel, self.inputs[channel], state))

        if state:
            rising(channel)
        else:
            falling(channel)

def get_status_door(door):

    doors = [
       [ SWITCH0, 'Collecteur oeuf' ],
       [ SWITCH1, 'Porte enclos' ],
       [ SWITCH2, 'Porte jardin' ],
    ]

    io, desc = doors[door]

    return ("%s: %s" % (desc, 'ouvert' if GPIO.input(io) else 'ferme'))

def get_string_from_lux(lux):
    string = ''
    if 0 < lux < 0.3:
        string = dialog.lux_map[0]
    elif 2.3 < lux < 2.6:
        string = dialog.lux_map[1]
    elif 2.6 < lux < 5:
        string = dialog.lux_map[2]
    return '%0.1f%s' % (lux, (' (' + string + ')' if string else ''))

def get_string_from_temperatures(*args):
    string = []
    for i, temp in enumerate(args):
        if temp and -20 < temp < 50:
            sensor = dialog.sensors_map[i] + ': ' if len(dialog.sensors_map) > i else ''
            string.append('%s%0.1f°C' % (sensor, temp))
    return ', '.join(string)

#def read_input():
#    return [ GPIO.input(GPIOS[index]) for index in range(0, 6) ]

def get_sensor_data():
    values = sensor.getLastValue(('vbatt', 'lux', 'temp', 'current', '1w_0', '1w_1', '1w_2'), maxage=config.MAX_AGE)
    vbatt, lux, temp, current = values['vbatt'], values['lux'], values['temp'], values['current']
    temp1, temp2, temp3 = values['1w_0'], values['1w_1'], values['1w_2']

    logger.debug("Vin: %0.2fV, A: %0.2fA, lux: %s, Temperatures -> %s, Portes -> %s, %s, %s" % \
        (vbatt, current, get_string_from_lux(lux), get_string_from_temperatures(temp, temp1, temp2, temp3), get_status_door(0), get_status_door(1), get_status_door(2)))

    return (vbatt, lux, temp, current, temp1, temp2, temp3)

def twit_report(vbatt, lux, temp, current, temp1, temp2, temp3, takephoto=True):
    twit(dialog.report % (get_string_from_temperatures(temp, temp1, temp2, temp3), get_string_from_lux(lux), vbatt, current), takephoto=takephoto)

class Report(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

    def stop(self):
        self._stopevent.set()

    def run(self):

        # Update your status
        #twit('@%s Application start !' % config.TWITTER_ADMIN_ACCOUNT)

        counter = 0

        while not self._stopevent.isSet():
            counter += 1

            # Send tweet every 3 hours
            if counter == 60 * 3:
                sensors_data = get_sensor_data()
                twit_report(*sensors_data)
                counter = 0

            time.sleep(60)

if __name__ == "__main__":

    print(__doc__)

    if config.TWITTER_ON:
        twt = Twython(secret.TWITTER_CONSUMER_KEY, secret.TWITTER_CONSUMER_SECRET, secret.TWITTER_OAUTH_TOKEN, secret.TWITTER_OAUTH_SECRET)

    '''
    Sensors thread
    '''
    sensor.start()

    # Wait while all sensor not ready !
    print('Waiting for sensors ready...', end='')
    sensor.waitForSensorsReady(('vbatt', 'current', 'lux', 'temp'))

    while not pira.isReady():
        time.sleep(1)

    print('Ok !')

    '''
    Configure misc
    '''
    cam = Camera()
    cam.setCallback(IR_ON, IR_OFF)

    events = Events()

    if config.TWITTER_ON:
        tthread = Twitter(twt)
        tthread.start()

    help_string = '''La vie de poule

 ?  This help
 c  Reload config
 p  Capture image and send to Twitter
 r  Send report to Twitter
 v  Modify verbosity
 d  Get sensor data
 t  Toggle relay
 l  Toggle led
 q  Exit
'''

    if config.FAKE_MODE:
        help_string += '''
Only in fake mode :
 0  Generate fake input on switch 0
 1  Generate fake input on switch 1
 2  Generate fake input on switch 2
 3  Generate PIR event
 4  Generate voltage threshold alert
 5  Generate current threshold alert
 6  Generate temperature threshold alert
'''

    kb = KBHit()

    print('Hit q key to exit, ? for help !')

    inputs = {
        '0': [ True, events.door0_falling, events.door0_rising, SWITCH0 ],
        '1': [ True, events.door1_falling, events.door1_rising, SWITCH1 ],
        '2': [ True, events.door2_falling, events.door2_rising, SWITCH2 ],
    }

    rthread = Report()
    rthread.start()

    while True:

        if kb.kbhit():
            c = kb.getch()
            if c == '?':
                print(help_string)
            elif c == 'q':
                print('Quit...')
                if 'rthread' in globals():
                    rthread.stop()
                if 'tthread' in globals():
                    tthread.stop()
                sensor.stop()
                break
            elif c == 'c':
                print('Reload config !')
                reload(config)
            elif c == 'p':
                twit('Cheese !', takephoto=True)
            elif c == 'r':
                sensors_data = get_sensor_data()
                twit_report(*sensors_data, takephoto=False)
            elif c == 'd':
                get_sensor_data()
            elif c == 't':
                GPIO.output(RELAY, not GPIO.input(RELAY))
                logger.info('Toggle relay (%s) !' % ('on' if not GPIO.input(RELAY) else 'off'))
            elif c == 'l':
                GPIO.output(LED, not GPIO.input(LED))
                logger.info('Toggle led (%s) !' % ('on' if GPIO.input(LED) else 'off'))
            elif c == 'v':
                levels = [ logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL ]
                index = levels.index(logger.getEffectiveLevel()) + 1
                if index >= len(levels):
                    index = 0
                logger.setLevel(levels[index])
                print('Set level to %s !' % (logging.getLevelName(levels[index])))

            if config.FAKE_MODE:
                if c in inputs:
                    value, falling, rising, arg = inputs[c]
                    (falling if inputs[c][0] else rising)(arg)
                    inputs[c][0] = not inputs[c][0]
                elif c == '3':
                    events.pir(PIR)
                elif c.isdigit() and 3 < int(c) < 7:
                    name, value, validrange = (
                        ( 'vbatt',      9,      config.VOLTAGE_ALERT ),
                        ( 'current',    0.29,   config.CURRENT_ALERT ),
                        ( 'temp',       2,      config.TEMP_ALERT )
                    )[int(c) - 4]

                    alerts(name, value, validrange)

        # Collecteur oeuf ouvert ?
        if GPIO.input(SWITCH0):
            # Status led blinking
            for status in (True, False) * 6:
                GPIO.output(LED, status)
                time.sleep(0.5)
        else:
            time.sleep(3)

    kb.set_normal_term()

