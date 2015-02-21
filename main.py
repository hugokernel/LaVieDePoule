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
import os
import time
import arrow
import logging
import re
import threading
from datetime import datetime

try:
    reload

    # Python 2.x related problem with utf-8
    reload(sys)  
    sys.setdefaultencoding('utf8')
except NameError:
    from importlib import reload

from lib.kbhit import KBHit
from lib.RainbowHandler import RainbowLoggingHandler
from lib.freesms import send_sms

from core.db import TwitterActivityTable, EventsTable, SensorsTable, EggsTable, sqla, db
from core.functions import only_one_call_each, get_time
from core.sensors import Sensors
from core.speak import speak
from core import dialog

from config import general as config, secret, camera as config_camera

if config.FAKE_MODE:
    from core.fake import (  PiCamera, GPIO,
                            Twython, TwythonError, TwythonRateLimitError, TwythonAuthError,
                            onewire_read_temperature, Raspiomix as Raspiomix_Origin,
                            Camera )
else:
    from lib.raspiomix import Raspiomix as Raspiomix_Origin
    from core.camera import Camera
    from twython import Twython, TwythonError, TwythonRateLimitError, TwythonAuthError
    from picamera import PiCamera
    import RPi.GPIO as GPIO
    from core.functions import onewire_read_temperature
    from eggcounter import scan_image_with_config_file

    if config.SERVER_ON:
        from www import start as webstart

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

IR_ON   = lambda: GPIO.output(RELAY, False)
IR_OFF  = lambda: GPIO.output(RELAY, True)
IR_OFF()

'''
IR_ON()
time.sleep(5)
print('start')
cam = Camera()
cam.setCallback(IR_ON, IR_OFF)
cam.takePhoto(filename='/tmp/paf.jpg', low_light=True)

sys.exit()
'''

def sms(message):
    logger.debug("Send sms with message : %s" % message)
    send_sms(secret.FREESMS_LOGIN, secret.FREESMS_KEY, 'Poulailler: ' + message)

class PirActivity():

    # Interval in second
    interval = 30.0

    activities = []
    startat = False

    def __init__(self):
        self.startat = time.time()

    def add(self):
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

sensor = Sensors(1 if config.FAKE_MODE else 2 * 60)

def get_maxima(name):
    c = SensorsTable.c
    query = sqla.select([c.name, sqla.sql.func.min(sqla.cast(c.value, sqla.Float)), \
        sqla.sql.func.max(sqla.cast(c.value, sqla.Float)), c.type ]).group_by(c.type, c.name). \
        where(c.name==name)
    name, _min, _max, type = db.execute(query).fetchone()
    return (_min, _max)

class Maxmin:
    '''Detect maxim temperature
    '''

    sensor_name = '1w_0'

    minima_detected = None
    maxima_detected = None

    @staticmethod
    @sensor.changedetect(name=sensor_name)
    def detect_increase(name, value):
        if Maxmin.minima_detected is not None:
            _min, _ = get_maxima(name)
            twit(dialog.record_out_temp_min % (_min, Maxmin.minima_detected.humanize(locale='fr')))
            Maxmin.minima_detected = None

    @staticmethod
    @sensor.changedetect(name=sensor_name, speed=-0.01)
    def detect_decrease(name, value):
        if Maxmin.maxima_detected is not None:
            _, _max = get_maxima(name)
            twit(dialog.record_out_temp_max % (_max, Maxmin.maxima_detected.humanize(locale='fr')))
            Maxmin.maxima_detected = None

    @staticmethod
    @sensor.threshold(get_maxima, sensor_name)
    def detect_maxima(name, value, threshold):
        _min, _max = threshold
        if value < _min:
            Maxmin.minima_detected = arrow.utcnow()
        elif value > _max:
            Maxmin.maxima_detected = arrow.utcnow()

@sensor.ready()
@only_one_call_each(seconds=config.SAVE_TO_DB_EVERY, withposarg=0)
def savetodb(name, value):
    _, _, _, type = sensor.sensors[name]
    db.execute(SensorsTable.insert().values(
        type=type,
        name=name,
        value=value,
        date=datetime.now(),
    ))

@sensor.notinrange()
def notinrange(name, value, validrange):
    logger.error("%s sensor not in valid range (%d, range: %s) !" % (name, value, validrange))

'''
@sensor.threshold((0, 4), 'pir')
def detect_activity(name, value, threshold):
    logger.info('Activity detected (%s) !' % value)
    logger.info('Lux: %s' % sensor.getLastValue('lux'))
'''

class Nest:
    '''Detect hen in nest !
    '''

    names = ('1w_1', '1w_2')
    increase = {}
    for name in names:
        increase[name] = None

    @staticmethod
    @sensor.changedetect(name=names, speed=0.3)
    def detectIncrease(name, value):
        logger.info('Increase detected (%s) !' % name)

        if Nest.increase[name] is not None:
            if not Nest.increase[name]:
                twit(dialog.egglay_detected, takephoto=True, nest_index=name[-1])

        Nest.increase[name] = True

    @staticmethod
    @sensor.changedetect(name=names, speed=-0.2)
    def detectDecrease(name, value):
        logger.info('Decrease detected (%s) !' % name)

        if Nest.increase[name] is not None:
            if Nest.increase[name]:
                logger.warn('Poule sorti du nid %i !' % int(name[-1]))

                tthread.eggScan(onlynest=int(name[-1]))

        Nest.increase[name] = False

@sensor.threshold(config.TEMP_ALERT,    'temp')
@sensor.threshold(config.VOLTAGE_ALERT, 'vbatt')
@sensor.threshold(config.CURRENT_ALERT, 'current')
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
        return

    if config.TWITTER_ON:
        twit(('@%s ' % config.TWITTER_ADMIN_ACCOUNT) + message)
    
    sms(message)

def adc_read_average(io, times=5):
    value = 0.0
    for i in range(times):
        value += raspi.readAdc(io)
    return value / i

sensor.declare('vbatt',      lambda: raspi.readAdc(0) / 0.354,    type=sensor.TYPE_VOLTAGE)
sensor.declare('current',    lambda: raspi.readAdc(3) * 10 / 6.8, type='current')
sensor.declare('lux',        lambda: adc_read_average(1),         type='luminosity')

with sensor.attributes(type='switch'):
    sensor.declare('door0',      lambda: GPIO.input(SWITCH0))
    sensor.declare('door1',      lambda: GPIO.input(SWITCH1))
    sensor.declare('door2',      lambda: GPIO.input(SWITCH2))

TEMP_VALID_RANGE = (-30, 50)
def read_onewire(address, maxretry=5, validrange=TEMP_VALID_RANGE):
    retry = 0
    while True:
        result = onewire_read_temperature(address)
        if validrange[0] < result < validrange[1]:
            return result
        retry += 1
        if retry >= maxretry:
            return None

with sensor.attributes(validrange=TEMP_VALID_RANGE, type=sensor.TYPE_TEMPERATURE):
    sensor.declare('temp',   lambda: raspi.readAdc(2) * 100)         # Enceinte
    sensor.declare('1w_0',   read_onewire, config.ONEWIRE_SENSOR2)   # Extérieur
    sensor.declare('1w_1',   read_onewire, config.ONEWIRE_SENSOR1)   # Nid 1
    sensor.declare('1w_2',   read_onewire, config.ONEWIRE_SENSOR0)   # Nid 2

sensor.declare('pir',   pira.get, type='activity')

#sensor.setNotInRangeCallback(lambda name, value, validrange: logger.error("%s sensor not in valid range (%d, range: %s) !" % (name, value, validrange)))
#sensor.setReadyCallback(detect_increase, '1w_1')

"""
@sensor.if_value(name='1w_2', lower=12)
def toto():
    print('ok!')

sensor.start()
while True:
    print(sensor.getLastValue('1w_2'))
    toto()
    time.sleep(1)
"""

'''
for i in range(0, 20):
    detect_increase(i)

for i in range(0, 20):
    detect_increase(i)
'''


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
    elif 2.3 < lux <= 2.6:
        string = dialog.lux_map[1]
    elif 2.6 < lux < 5:
        string = dialog.lux_map[2]
    return '%0.3f%s' % (lux, (' (' + string + ')' if string else ''))

def get_string_from_temperatures(*args):
    string = []
    for i, temp in enumerate(args):
        if temp and -20 < temp < 50:
            sensor = dialog.sensors_map[i] + ': ' if len(dialog.sensors_map) > i else ''
            string.append('%s%0.1f°C' % (sensor, temp))
    return ', '.join(string)

class Egg:

    image_directory = config.EGG_IMAGE_DIRECTORY

    export_file = '/tmp/egg_found.png'

    resolution = config_camera.default['resolution']

    camera = None

    def __init__(self, camera):
        self.camera = camera

    def isNew(self, position, tolerance=15):
        x, y = position
        c = EggsTable.c
        query = sqla.select([ c.id, c.x, c.y ]).where(c.date==str(datetime.now())[0:10])
        for line in db.execute(query).fetchall():
            if line[1] - tolerance <= x <= line[1] + tolerance and \
               line[2] - tolerance <= y <= line[2] + tolerance:
                return False
        return True

    def getNestFromPosition(self, position):
        return 1 if position[0] >= self.resolution[0] else 2

    def scan(self, support_file=None, saveindb=True, onlynest=None):
        """Scan for eggs
        - support_file  : File use to draw egg detection
        - saveindb      : Save in db egg detected
        - onlynest      : Scan only in this nest
        """
        unknow = []
        input_file = os.path.join(self.image_directory, str(datetime.now()) + '.png')

        logger.debug('Start egg scan')

        # Capture image
        self.camera.takePhoto(filename=input_file, configuration=config_camera.egg_detection)

        params = {
            'input_file':   input_file,
            'export_file':  self.export_file,
            'verbose':      False
        }

        if support_file:
            params['support_file'] = support_file

        # Now, scan image
        eggs_found = scan_image_with_config_file('config/egg.ini', **params)

        if len(eggs_found):
            logger.debug('Egg(s) found (%s) !' % (str(eggs_found)))

            unknow = []
            for position in eggs_found:

                if onlynest and self.getNestFromPosition(position) != onlynest:
                    continue

                if self.isNew(position):
                    unknow.append(position)

                    # Insert in db
                    if saveindb:
                        db.execute(EggsTable.insert().values(
                            x=position[0],
                            y=position[1],
                            date=datetime.now(),
                        ))

        if len(unknow):
            logger.debug('New egg(s) found (%s) !' % (str(unknow)))
            sms("Un nouvel oeuf est là !")
        else:
            logger.debug('No egg found !')

        return (len(unknow), [ self.getNestFromPosition(pos) for pos in unknow ])

class Twitter(threading.Thread):

    PERIOD = 60 * 4

    sources = []
    twitter = None
    egg = None

    def __init__(self, twitter, egg):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

        self.twitter = twitter
        self.egg = egg

        # Load all response
        s = sqla.select([TwitterActivityTable.c.source_id])
        for id, in db.execute(s):
            self.sources.append(id)

    def stop(self):
        self._stopevent.set()

    def markProcessed(self, mention, response):

        str2dtime = lambda date: datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')

        db.execute(TwitterActivityTable.insert().values(
            source_id=mention['id_str'],
            source_reply_id=mention['in_reply_to_status_id'],
            source_user_name=mention['user']['screen_name'],
            source_content=mention['text'],
            source_date=str2dtime(mention['created_at']),
            reply_id=response['id_str'],
            reply_content=response['text'],
            reply_date=str2dtime(response['created_at']),
        ))

        self.sources.append(int(mention['id_str']))

    def commands(self, mention):
        '''
        mention = ' '.join(sys.argv[1:])

        Syntax:
        @LaVieDePoule !photo
        @LaVieDePoule !photo(iroff)
        @LaVieDePoule !plot(2014-12-01 2014-12-31)
        '''

        status = False

        # Try to catch without parenthese
        #m = re.search(r'@([A-Za-z0-9_]{1,15})+\s\!([a-z_]+)\s*(.*?)*$', mention)
        m = re.search(r'@([A-Za-z0-9_]{1,15})+\s\!([a-z_]+)\s*(.*?)$', mention['text'])
        if m:
            dest, cmd, cmdargs, args = m.group(1), m.group(2), [], m.group(3).split()

        if not m:
            m = re.search(r'@([A-Za-z0-9_]{1,15})+\s\!([a-z_]+)\((.*?)\)(.*?)$', mention['text'])
            if m:
                dest, cmd, cmdargs, args = m.group(1), m.group(2), m.group(3).split(), m.group(4).split()
            else:
                return status

        def cmd_photo(*args):
            '''
            Take a photo
            '''
            if cam.takePhoto():
                return 'Cheese !', cam.photo_file

        def cmd_sensor(*args):
            '''
            Get data from all or from some sensors
            '''
            if not args:
                vbatt, lux, temp, current, temp1, temp2, temp3 = get_sensor_data()
                return dialog.report % (get_string_from_temperatures(temp, temp1, temp2, temp3), get_string_from_lux(lux), vbatt, current), None
            else:
                nargs = []
                for arg in args:
                    try:
                        tmp = {
                            'nid2': '1w_0',
                            'nid1': '1w_1',
                            'ext':  '1w_2'
                        }[arg]
                    except KeyError:
                        tmp = arg

                    if tmp not in nargs:
                        nargs.append(tmp)

                values = sensor.getLastValue(nargs)
                return ', '.join([ name + ': ' + str(value) for name, value in values.items() ]), None

        def cmd_help(*args):
            '''
            Get all available command
            '''
            return 'Help: ' + str([ command for command in commands ]), None

        def cmd_plot(*args):
            '''
            Generate plot and send it
            '''
            from plot import generate_plot_from_range, EXPORT_FILE
            start, end = args[0], args[1]
            status = generate_plot_from_range((start, end), dateformat='%d %b %H:%M')
            return 'Data from %s to %s' % (start, end), EXPORT_FILE

        commands = {
            'help':     cmd_help,
            'photo':    cmd_photo,
            'sensor':   cmd_sensor,
            'plot':     cmd_plot,
        }

        if not cmd in commands:
            cmd = 'help'

        message, media = None, None
        data = commands[cmd](*cmdargs)
        if data:
            message, media = data

        if not message:
            return status

        if mention['user']['screen_name'] != config.TWITTER_ADMIN_ACCOUNT or not '+toall' in args:
            message = u'@%s %s' % (mention['user']['screen_name'], message)

        if message:
            status = self.response(mention, message, media)

        return status

    def response(self, mention, message, media=None):

        status = False

        logger.info('Sending response to twitter mention from %s, reponse: %s' % (mention['user']['screen_name'], message))

        try:
            args = {
                'status':                   message,
                'in_reply_to_status_id':    mention['id_str']
            }
            func = self.twitter.update_status

            if media:
                args['media'] = open(media, 'r')
                func = self.twitter.update_status_with_media

            response = func(**args)

            status = True
        except (TwythonError, TwythonRateLimitError) as e:
            logger.error(e)

        self.markProcessed(mention, response)

        return status

    @only_one_call_each(hours=6, startin=60 * 60 * 6)
    def report(self):
        twit_report(*get_sensor_data())

    @only_one_call_each(hours=2) #minuts=30)
    @sensor.if_value(name='lux', greater=1)
    def eggScan(self, onlynest=None):
        # Scan egg !
        support_file = '/tmp/egg_support_file.jpg'
        cam.takePhoto(filename=support_file)

        egg_count, nests = self.egg.scan(support_file, onlynest=onlynest)
        if egg_count > 0:
            message, params = (dialog.egg_detected, { 'nest_index': nests[0] }) if egg_count == 1 \
                else (dialog.eggs_detected, { 'count': egg_count })
            self.twitter.update_status_with_media(status=speak(message, **params), media=open(self.egg.export_file, 'r'))

    def run(self):

        while not self._stopevent.isSet():

            self.report()

            try:
                mentions = self.twitter.get_mentions_timeline()
            except TwythonAuthError as e:
                logger.error(e)
                time.sleep(60)
                continue

            for mention in mentions:

                # Skip if mention is already processed
                if int(mention['id_str']) in self.sources:
                    continue

                # Test if there are a command
                if mention['user']['screen_name'] == config.TWITTER_ADMIN_ACCOUNT:
                    if self.commands(mention):
                        continue

                # Answer mention contains 'cot'
                if 'cot' in mention['text'].lower():
                    self.response(mention, speak(dialog.cot, username=mention['user']['screen_name']))
                    continue

            self.eggScan()

            time.sleep(self.PERIOD)

def twit(message, takephoto=False, takevideo=False, videolength=10, **kwargs):
    message = speak(message, **kwargs) if type(message) == tuple else message

    logger.info('Twit: %s (takephoto: %i, takevideo: %i)' % (message, takephoto, takevideo))

    if config.TWITTER_ON:
        try:
            if takephoto:
                if cam.takePhoto():
                    twt.update_status_with_media(status=message, media=open(cam.photo_file, 'r'))
            elif takevideo:
                if cam.takeVideo(videolength):
                    twt.update_status_with_media(status=message, media=open(cam.video_file, 'r'))
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
        # Disabled ! (because too many bad detection !)
        return
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


'''
if 'webstart' in globals():
    webstart(host=config.SERVER_HOST, port=config.SERVER_PORT, debug=config.FAKE_MODE)

while True:
    time.sleep(2)
'''


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
    cam = Camera(photo_configuration=config_camera.default, video_configuration=config_camera.video)
    cam.setCallback(IR_ON, IR_OFF)

    events = Events()

    if 'webapp' in globals():
        webstart(host=config.WEBSERVER_HOST, port=config.WEBSERVER_PORT)

    # Egg scanner
    egg = Egg(cam)

    if config.TWITTER_ON:
        tthread = Twitter(twt, egg)
        tthread.start()

    help_string = '''La vie de poule

 ?  This help
 c  Reload config
 v  Modify verbosity
 d  Get sensor data
 t  Toggle relay
 l  Toggle led
 e  Run an egg scan

 Twitter related :
 R  Send report
 P  Capture image and send it

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

    while True:

        if kb.kbhit():
            c = kb.getch()
            if c == '?':
                print(help_string)
            elif c == 'q':
                print('Quit...')
                if 'tthread' in globals():
                    tthread.stop()
                sensor.stop()
                break
            elif c == 'c':
                print('Reload config !')
                reload(config)

                # Dump config
                print('\n'.join([ '%s: %s' % (name, getattr(config, name)) for name in dir(config) if name[0:2] != '__' ]))
            elif c == 'P':
                twit('Cheese !', takephoto=True)
            elif c == 'R':
                sensors_data = get_sensor_data()
                twit_report(*sensors_data, takephoto=False)
            #elif c == 'V':
            #    twit(dialog.live_video, takevideo=True)
            elif c == 'd':
                get_sensor_data()
            elif c == 't':
                GPIO.output(RELAY, not GPIO.input(RELAY))
                logger.info('Toggle relay (%s) !' % ('on' if not GPIO.input(RELAY) else 'off'))
            elif c == 'l':
                GPIO.output(LED, not GPIO.input(LED))
                logger.info('Toggle led (%s) !' % ('on' if GPIO.input(LED) else 'off'))
            elif c == 'e':
                egg_count, nests = egg.scan(saveindb=False)
                logger.info('Egg found : %i (%s)' % (egg_count, str(nests)))
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

