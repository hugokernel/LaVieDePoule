
class Twython():
    def __init__(self, consumer_key, consumer_secret, oauth_token, oauth_secret):
        pass
    def update_status(self, status, media=None):
        pass
    def update_status_with_media(self, status, media):
        pass

class TwythonError(Exception):
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
    def add_event_detect(a, b, callback, bouncetime):
        pass

    @staticmethod
    def input(index):
        GPIO.toggle = not GPIO.toggle
        return GPIO.toggle

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

