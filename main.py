# -*- coding: utf8 -*-

"""
.____         ____   ___.__       ________        __________            .__
|    |   _____\   \ /   |__| ____ \______ \   ____\______   \____  __ __|  |   ____
|    |   \__  \\   Y   /|  _/ __ \ |    |  \_/ __ \|     ___/  _ \|  |  |  | _/ __ \
|    |___ / __ \\     / |  \  ___/ |    `   \  ___/|    |  (  <_> |  |  |  |_\  ___/
|_______ (____  /\___/  |__|\___  /_______  /\___  |____|   \____/|____/|____/\___  >
        \/    \/                \/        \/     \/                               \/"""

import sys
import time
import logging
import curses
from fractions import Fraction
import threading
from datetime import datetime

import dialog

import sqlalchemy as sa

from lib.kbhit import KBHit
from lib.raspiomix import Raspiomix as Raspiomix_Origin
from lib.RainbowHandler import RainbowLoggingHandler
from lib.speak import speak
from lib.freesms import send_sms

from config import general as config
from config import secret

if config.FAKE_MODE:
    from fake import PiCamera, GPIO, Twython, TwythonError, TwythonRateLimitError, read_w1_temperature
else:
    from twython import Twython, TwythonError, TwythonRateLimitError
    from picamera import PiCamera
    import RPi.GPIO as GPIO
    from functions import read_w1_temperature

from functions import elapsed_time

logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

rainbowHandler = RainbowLoggingHandler(sys.stdout)
rainbowHandler.setFormatter(formatter)
logger.addHandler(rainbowHandler)

fileHandler = logging.FileHandler('laviedepoule.log')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

logger.setLevel(logging.DEBUG)

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

t = Twython(secret.TWITTER_CONSUMER_KEY, secret.TWITTER_CONSUMER_SECRET, secret.TWITTER_OAUTH_TOKEN, secret.TWITTER_OAUTH_SECRET)
#t = None

db = sa.create_engine('sqlite:///data.sqlite')
db.echo = False

metadata = sa.MetaData()
TwitterActivityTable = sa.Table('twitter_activity', metadata,
    sa.Column('id',                 sa.Integer, primary_key=True),
    sa.Column('source_id',          sa.Integer),
    sa.Column('source_reply_id',    sa.Integer),
    sa.Column('source_user_name',   sa.String(255)),
    sa.Column('source_content',     sa.String(160)),
    sa.Column('source_date',        sa.DateTime),
    sa.Column('reply_id',           sa.Integer),
    sa.Column('reply_content',      sa.String(160)),
    sa.Column('reply_date',         sa.DateTime),
)

EventsTable = sa.Table('events', metadata,
    sa.Column('id',     sa.Integer, primary_key=True),
    sa.Column('input',  sa.Integer),
    sa.Column('type',   sa.String(160)),
    sa.Column('date',   sa.DateTime),
)

SensorsTable = sa.Table('sensors', metadata,
    sa.Column('id',     sa.Integer, primary_key=True),
    sa.Column('type',   sa.String(16)),
    sa.Column('name',   sa.String(32)),
    sa.Column('value',  sa.String(128)),
    sa.Column('date',   sa.DateTime),
)

metadata.create_all(db)

'''
class Sensors(threading.Thread):

    sensors = {}
    results = {}

    def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

    def stop(self):
        self._stopevent.set()

    def declare(self, name, callback, params=None):
        self.sensors[name] = (callback, params)

    def get(self, name):
        return self.results if name in self.results else None

    def run(self):
        while not self._stopevent.isSet():

            # Read all sensors data
            print(self.sensors)
            for name, data in self.sensors.items():
                callback, params = data

                self.results[name] = callback()

            time.sleep(2)

def toto():
    return 1

s = Sensors()
s.declare('toto', toto)
s.run()

while True:
    print(s.get('toto'))
    time.sleep(1)
'''

class Twitter(threading.Thread):

    sources = []
    twitter = None

    def __init__(self, twitter):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

        self.twitter = twitter

        # Load all response
        s = sa.select([TwitterActivityTable.c.source_id])
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

            time.sleep(60)

tthread = Twitter(t)
tthread.start()

'''
# Get your "home" timeline
t.statuses.home_timeline()

# Get a particular friend's timeline
t.statuses.user_timeline(screen_name="billybob")

# to pass in GET/POST parameters, such as `count`
t.statuses.home_timeline(count=5)

# to pass in the GET/POST parameter `id` you need to use `_id`
t.statuses.oembed(_id=1234567890)

# Send a direct message
t.direct_messages.new(
    user="billybob",
    text="I think yer swell!")
'''

def get_time(seconds):
    return elapsed_time(seconds, ['année', 'semaine', 'jour', 'heure', 'minute', 'seconde'], add_s=True)

def twit(message, takephoto=False, **kwargs):
    global t

    message = speak(message, **kwargs) if type(message) == tuple else message

    if config.FAKE_MODE:
        logger.info('Twit: %s' % message)
    else:
        logger.debug('Twit: %s' % message)
        if takephoto:
            IR_ON()
            with PiCamera() as camera:
                camera.resolution = (1024, 768)

                if config.LOW_LIGHT:
                    camera.framerate = Fraction(1, 6)
                    camera.shutter_speed = 6000000
                    #camera.exposure_mode = 'off'
                    camera.ISO = 800
                    # Give the camera a good long time to measure AWB
                    # (you may wish to use fixed AWB instead)
                    time.sleep(10)

                camera.capture('image.jpg')

                photo = open('image.jpg', 'rb')
            IR_OFF()

        if t:
            try:
                if takephoto:
                    t.update_status_with_media(status=message, media=photo)
                else:
                    t.update_status(status=message)
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
        self.pir_counter += 1 if times[0] < 1 else -self.pir_counter
        print('Pir !', times, self.pir_counter)
        if self.pir_counter == 2:
            self.saveLog(channel)
            logger.debug("Pir event detected !")
            self.pir_counter = 0

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

events = Events()

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
        if -20 < temp < 50:
            sensor = dialog.sensors_map[i] + ': ' if len(dialog.sensors_map) > i else ''
            string.append('%s%0.1f°C' % (sensor, temp))
    return ', '.join(string)

def read_input():
    return [ GPIO.input(GPIOS[index]) for index in range(0, 6) ]

alerts = (
    ( config.VOLTAGE_ALERT, 'Vbatt voltage (%0.2fV) not in range (thresholds: %s) !'),
    ( config.CURRENT_ALERT, 'Current (%0.2fA) not in range (thresholds: %s) !'),
    ( config.TEMP_ALERT,    'Main temperature (%i°C) not in range (thresholds: %s) !')
)

'''
def twit_and_sms(message):
    twit(('@%s ' % config.TWITTER_ADMIN_ACCOUNT) + message)
    send_sms(secret.FREESMS_LOGIN, secret.FREESMS_KEY, 'Poulailler: ' message)
'''

def thresholds_test(values, alerts, force=None, last=[]):
    out = []
    index = 0
    for thresholds, message in alerts:
        # Only first alert, skip other !
        if index not in last and (not config.FAKE_MODE and not thresholds[0] < values[index] < thresholds[1] or force is not None and force == index):
            message = message % (values[index], thresholds)

            if config.FAKE_MODE:
                logger.info(message)
            else:
                twit(('@%s ' % config.TWITTER_ADMIN_ACCOUNT) + message)
                send_sms(secret.FREESMS_LOGIN, secret.FREESMS_KEY, 'Poulailler: ' + message)

            out.append(index)

            if index not in last:
                last.append(index)
        index += 1

    if not out:
        last = []

    return out

def get_sensor_data():
    analog = raspi.readAdc()
    #vbatt, vpan, temp, current = analog[0] / 0.354, analog[1] / 0.167, analog[2] * 100, analog[3] * 10 / 6.8
    vbatt, lux, temp, current = analog[0] / 0.354, analog[1], analog[2] * 100, analog[3] * 10 / 6.8
    temp1, temp2, temp3 = read_w1_temperature([0, 1, 2])

    logger.debug("Vin: %0.2fV, A: %0.2fA, lux: %s, Temperatures -> %s, Portes -> %s, %s, %s" % \
        (vbatt, current, get_string_from_lux(lux), get_string_from_temperatures(temp, temp1, temp2, temp3), get_status_door(0), get_status_door(1), get_status_door(2)))

    return (vbatt, lux, temp, current, temp1, temp2, temp3)

def twit_report(vbatt, lux, temp, current, temp1, temp2, temp3, takephoto=True):
    #twit(dialog.report_light % (temp, lux, vbatt, current), takephoto=takephoto)

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

            sensors_data = get_sensor_data()
            vbatt, lux, temp, current, temp1, temp2, temp3 = sensors_data

            # Test thresholds
            thresholds_test([vbatt, current, temp], alerts)

            counter += 1

            # Send tweet every 3 hours
            if counter == 60 * 3:
                twit_report(*sensors_data)
                counter = 0

            time.sleep(60)

if __name__ == "__main__":

    print(__doc__)

    help_string = '''La vie de poule

 ?  This help
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

    print('Hit any key, or ESC to exit')

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
                break
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
                    thresholds_test([9, 0.29, 2], alerts, int(c) - 4)

        # Collecteur oeuf ouvert ?
        if GPIO.input(SWITCH0):
            # Status led blinking
            for status in (True, False) * 6:
                GPIO.output(LED, status)
                time.sleep(0.5)
        else:
            time.sleep(3)

    kb.set_normal_term()

