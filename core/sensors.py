
import sys
import time
import threading
from contextlib import contextmanager
import collections

class FifoBuffer:
    
    default = None
    data = []

    def __init__(self, data=default, size=-1):
        self.data = data if data else [ self.default ] * size

    def isFull(self):
        for val in self.data:
            if val == self.default:
                return False
        return True

    def append(self, x):
        self.data.pop(0)
        self.data.append(x)

    def read(self):
        for data in self.data:
            yield data

class Sensors(threading.Thread):

    '''
    Wrapper for all sensor
    '''

    TYPE_TEMPERATURE = 'temperature'
    TYPE_VOLTAGE     = 'voltage'
    TYPE_CURRENT     = 'current'

    # Refresh period in second
    period = 60

    sensors = {}

    '''
    Stored last value with timestamp
    '''
    results = {}

    callbacks_ready = {}
    callbacks_threshold = {}
    callbacks_notinrange = {}

    default_validrange = None
    default_type = None

    def __init__(self, period=period):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

        self.period = period

    def stop(self):
        self._stopevent.set()

    def declare(self, name, callback, params=None, type=None, validrange=None):
        """Declare a sensor and his associated callback"""
        self.sensors[name] = (callback, params, validrange if validrange else self.default_validrange, type if type else self.default_type)
        self.results[name] = (None, None)

    def __getLastValue(self, name, maxage=0, withtimestamp=False):
        try:
            value, timestamp = self.results[name]
            if not maxage or not timestamp or time.time() - timestamp <= maxage:
                return (value, timestamp) if withtimestamp else value
        except KeyError:
            pass
        return (None, None) if withtimestamp else None

    def getLastValue(self, name=None, maxage=0, withtimestamp=False):
        """Get last value read from sensor

        Multiple format for name parameter :
        - name is str : Get value with name 'name'
        - name is list or tuple : Get all values with name in list/tuple
        - name is None : Get all values
        """
        if name and type(name) not in (list, tuple):
            name = (name, )

        out = {}
        for key in name if name else self.results:
            out[key] = self.__getLastValue(key, maxage, withtimestamp)
        return out

    def setReadyCallback(self, callback, name=None):
        """Callback called when data on channel read !"""
        if name not in self.callbacks_ready:
            self.callbacks_ready[name] = []

        self.callbacks_ready[name].append(callback)

    def setThresholdCallback(self, limits, callback, name=None):
        """Callback called when data on channel read !
        Value not in limits are saved !
        """
        if name not in self.callbacks_threshold:
            self.callbacks_threshold[name] = []

        self.callbacks_threshold[name].append((limits, callback))

    def setNotInRangeCallback(self, callback, name=None):
        """Callback called when data not in range !
        Not in range value are NOT saved !
        """
        if name not in self.callbacks_notinrange:
            self.callbacks_notinrange[name] = []

        self.callbacks_notinrange[name].append(callback)

    def isSensorsReady(self, sensors=[]):
        """Return if sensors is ready"""
        ready = True
        for sensor in sensors if sensors else self.sensors:
            if not sensor in self.results:
                ready = False
                break

            _, data = self.results[sensor]
            if data is None:
                ready = False
                break
        return ready

    def waitForSensorsReady(self, sensors):
        """Wait for sensors is ready"""
        while not self.isSensorsReady(sensors):
            time.sleep(1)

    def run(self):
        while not self._stopevent.isSet():
            # Read all sensors data
            for name, data in self.sensors.items():

                callback, params, validrange, _ = data
                if params:
                    #result = callback(*params if type(params) in (tuple, list) else params)
                    if type(params) in (tuple, list):
                        result = callback(*params)
                    elif type(params) is dict:
                        result = callback(**params)
                    else:
                        result = callback(params)
                else:
                    result = callback()

                # Todo: Handle case when result is None
                if result is None:
                    continue

                # Save only if in valid range !
                if validrange:
                    _min, _max = validrange(name) if callable(validrange) else validrange
                    if not (_min < result < _max):
                        for key in (None, name):
                            if key in self.callbacks_notinrange:
                                for callback in self.callbacks_notinrange[key]:
                                    callback(name, result, (_min, _max))
                        continue

                # Test threshold
                if name in self.callbacks_threshold:
                    for data in self.callbacks_threshold[name]:
                        threshold, callback = data
                        _min, _max = threshold(name) if callable(threshold) else threshold
                        if not (_min <= result <= _max):
                            callback(name, result, (_min, _max))

                # Call ready callbacks
                for key in (None, name):
                    if key in self.callbacks_ready:
                        for callback in self.callbacks_ready[key]:
                            callback(name, result)

                # All good ? Save value !
                self.results[name] = (result, time.time())

            time.sleep(self.period)

    @contextmanager
    def attributes(self, validrange=None, type=None):
        # Save context
        if validrange:
            old_validrange, self.default_validrange = self.default_validrange, validrange
        if type:
            old_type, self.default_type = self.default_type, type
        try:
            yield
        finally:
            # Restore context
            if validrange:
                self.default_validrange, validrange = old_validrange, self.default_validrange
            if type:
                self.default_type, type = old_type, self.default_type

    '''
    Decorators
    '''

    def changedetect(self, name, speed=0.01, measure_count=5, min_period=0):
        """Detect sensor value variation

        - speed: Speed of variation (in minut), negative value for decrease detection
        - measure_count: Count of successfully grow measures
        - min_period: Minimum period before first test

        For example:

            @changedetect('temperature', speed=1):
            def warn(name, value):
                print("Temperature increase detected (1deg by minut) !")
        """

        names = name if type(name) in (list, tuple) else (name,)

        speed_min, speed_max = speed if type(speed) in (tuple, list) else (speed, sys.maxsize)

        assert(speed_min < speed_max)

        compare = '__gt__' if speed_min > 0 else '__lt__'
        def decorator(func):
            fifo = {}
            def wrapper(name, value, last_time=type('X', (object,), { 'value': None })):

                if min_period and last_time.value and last_time.value + min_period > time.time():
                    return

                last_time.value = time.time()

                '''
                Detect change of value
                '''
                fifo[name].append(value)
                
                # Fifo full, start change detection !
                if fifo[name].isFull():
                    last = None
                    for x in fifo[name].read():
                        if last is not None:
                            if not getattr(float(x), compare)(last):
                                break

                            val = abs((x - last) / self.period * 60)
                            if speed_min > val or val > speed_max:
                                break

                        last = x
                    else:
                        return func(name, value)

            for name in names:
                fifo[name] = FifoBuffer(size=measure_count)
                self.setReadyCallback(wrapper, name)

            return wrapper
        return decorator

    def notinrange(self, name=None):
        def wrapper(func):
            self.setNotInRangeCallback(func, name=None)
            return func
        return wrapper

    def ready(self, name=None):
        def wrapper(func):
            self.setReadyCallback(func, name=None)
            return func
        return wrapper

    def threshold(self, limits, name):
        def wrapper(func):
            self.setThresholdCallback(limits, func, name)
            return func
        return wrapper

    def if_value(self, name, equal=None, greater=None, lower=None):
        '''Call a function if sensor is equal, lower or greater value
        Todo: implement maxage parameter
        '''
        params = {}
        for param, compare in (('equal', '__eq__'), ('lower', '__lt__'), ('greater', '__gt__')):
            params[compare] = locals()[param] if param in locals() else None

        def decorator(func):
            def wrapper(*args, **kwargs):
                #nonlocal equal, greater, lower
                isok = False
                #for param, compare in ( ('equal', '__eq__'), ('lower', '__lt__'), ('greater', '__gt__') ):
                #    val = locals()[param]
                for compare, val in params.items():
                    if val is None:
                        continue
                    isok = getattr(self.getLastValue(name)[name], compare)(val)
                    if not isok:
                        break
                if isok:
                    return func(*args, **kwargs)
            return wrapper

        return decorator

if __name__ == '__main__':
    sensor = Sensors(1)

    class Grow(threading.Thread):

        __value = 0

        def __init__(self):
            threading.Thread.__init__(self)
            self._stopevent = threading.Event()

        def stop(self):
            self._stopevent.set()

        def run(self):
            while not self._stopevent.isSet():
                self.__value += 0.005
                time.sleep(1)

        def value(self):
            return self.__value

    g = Grow()
    g.start()

    sensor.declare('grow', g.value)
    sensor.declare('grow2', lambda: 2)

    #@sensor.changedetect(name='grow', speed=(120, 133))
    #@sensor.changedetect(name='grow', speed=120)
    @sensor.changedetect(name=('grow', 'grow2'), speed=0.29)
    def detect_change(name, value):
        print('Change + detected !!!!!!!!!!!!')

    sensor.start()

    i = 0
    while True:
        try:
            a = sensor.getLastValue('grow')
            print('Grow value : ', a)
            time.sleep(3)
        except KeyboardInterrupt:
            g.stop(); sensor.stop()
            import sys; sys.exit()

