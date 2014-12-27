
class Twython():
    def __init__(self, consumer_key, consumer_secret, oauth_token, oauth_secret):
        pass
    def update_status(self, status, media=None):
        pass
    def update_status_with_media(self, status, media):
        pass
    def get_mentions_timeline(self):
        return []

class TwythonError(Exception):
    pass

class TwythonRateLimitError(TwythonError):
    pass

class PiCamera:

    resolution = (1024, 768)
    framerate = 0
    shutter_speed = 6000000
    exposure_mode = 'off'
    ISO = 800

    def capture(self, image):
        pass

    def __enter__(self):
        return self
    def __exit__(self, a, b, c):
        pass

class GPIO:

    BOARD = 1
    IN = 0
    OUT = 1

    RISING = 0
    FALLING = 0
    BOTH = 1

    PUD_UP = 0

    toggle = False

    @staticmethod
    def setmode(a):
        pass

    @staticmethod
    def setwarnings(a):
        pass

    @staticmethod
    def setup(a, b, pull_up_down=None):
        pass

    @staticmethod
    def add_event_detect(a, b, callback, bouncetime=0):
        pass

    @staticmethod
    def input(index):
        GPIO.toggle = not GPIO.toggle
        return GPIO.toggle

    @staticmethod
    def output(index, value):
        return

class i2c:
    @staticmethod
    def writing_bytes(address, config):
        pass
    @staticmethod
    def reading(address, count):
        pass

    class I2CMaster:
        def transaction(self, a):
            return [ [0, 1, 2, 3] ]
        def __enter__(self):
            return self
        def __exit__(self, a, b, c):
            pass

class adc:
    class adc:
        def __init__(self):
            pass

        def getVoltage(self, channel):
            return 0

        def getVoltages(self, channels=[0, 1, 2, 3]):
            out = []
            for channel in channels:
                out.append(self.getVoltage(channel))
            return out

_value = 10.2
def onewire_read_temperature(sensors, fahrenheit=False, maxretry=3, basedir=None):
    global _value
    _value += 0.1

    out = []
    if type(sensors) == str:
        out.append(_value)
    elif type(sensors) == list:
        out = [ _value ] * len(sensors)

    return out if not len(out) or type(sensors) == list else out[0]

class Raspiomix:

    IO0 = 12
    IO1 = 11
    IO2 = 13
    IO3 = 15

    DIP0 = 7
    DIP1 = 16

    I2C_ADC_ADDRESS = 0x6E
    I2C_RTC_ADDRESS = 0x68

    ADC_CHANNELS = [ 0x9C, 0xBC, 0xDC, 0xFC ]

    DEVICE = '/dev/ttyAMA0'

    def __init__(self):
        pass

    def readAdc(self, channels=(0, 1, 2, 3)):
        #data = [] * len(channels)
        _value = 0.1
        return [ x for x in channels ] if type(channels) == list else _value

    def readRtc(self):
        return '20%02d-%02d-%02dT%02d:%02d:%02d' % (data[6], data[5], data[4], data[2], data[1], data[0])

class Camera:
    def setCallback(self, callback_before=None, callback_after=None): pass
    def takePhoto(self, resolution=None): pass
    def takeVideo(self, resolution=None): pass

