
import time
import threading
from contextlib import contextmanager

class Sensors(threading.Thread):

    '''
    Wrapper for all sensor
    '''

    TYPE_TEMPERATURE = 'temperature'
    TYPE_VOLTAGE     = 'voltage'
    TYPE_CURRENT     = 'current'

    # Refresh period in second
    period = 60 * 5

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

    def __init__(self, period=60 * 5):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

        self.period = period

    def stop(self):
        self._stopevent.set()

    def declare(self, name, callback, params=None, type=None, validrange=None):
        '''
        Declare a sensor and his associated callback
        '''
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
        '''
        Get last value read
        Multiple format for name parameter :
        - name is str : Get value with name 'name'
        - name is list or tuple : Get all values with name in list/tuple
        - name is None : Get all values
        '''
        if name and type(name) not in (list, tuple):
            name = (name, )

        out = {}
        for key in name if name else self.results:
            out[key] = self.__getLastValue(key, maxage, withtimestamp)
        return out

    def setReadyCallback(self, callback, name=None):
        '''
        Callback called when data on channel read !
        '''
        try:
            self.callbacks_ready[name]
        except KeyError:
            self.callbacks_ready[name] = []

        self.callbacks_ready[name].append(callback)

    def setThresholdCallback(self, threshold, callback, name=None):
        '''
        Callback called when data on channel read !
        Not in threshold value are saved !
        '''
        try:
            self.callbacks_threshold[name]
        except KeyError:
            self.callbacks_threshold[name] = []

        self.callbacks_threshold[name].append((threshold, callback))

    def setNotInRangeCallback(self, callback, name=None):
        '''
        Callback called when data not in range !
        Not in range value are NOT saved !
        '''
        try:
            self.callbacks_notinrange[name]
        except KeyError:
            self.callbacks_notinrange[name] = []

        self.callbacks_notinrange[name].append(callback)

    def isSensorsReady(self, sensors=[]):
        '''
        Return if sensors is ready
        '''
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
        '''
        Wait for sensors is ready
        '''
        while not self.isSensorsReady(sensors):
            time.sleep(1)

    def run(self):
        while not self._stopevent.isSet():
            # Read all sensors data
            for name, data in self.sensors.items():

                callback, params, validrange, _ = data
                if params:
                    result = callback(*params)
                else:
                    result = callback()

                # Todo: Handle case when result is None
                if not result:
                    continue

                # Save only if in valid range !
                if validrange:
                    _min, _max = validrange
                    if not (_min < result < _max):
                        for key in (None, name):
                            if key in self.callbacks_notinrange:
                                for callback in self.callbacks_notinrange[key]:
                                    callback(name, result, validrange)
                        continue

                # Test threshold
                if name in self.callbacks_threshold:
                    for data in self.callbacks_threshold[name]:
                        threshold, callback = data
                        _min, _max = threshold
                        if not (_min < result < _max):
                            callback(name, result, threshold)

                # Call callback
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

    def __detect_increase_or_decrease(self, compare, name, unit_per_minut=None, measure_count=5):
        '''
        unit_per_minut: How many unit grow value per minut
        measure_count: Count of successfully grow measures
        '''
        def decorator(func):
            def wrapper(name, value, values=[None] * measure_count):
                from core.functions import FifoBuffer
                '''
                Detect increase of value
                '''
                fifo = FifoBuffer(data=values)
                fifo.append(value)

                coeff = unit_per_minut / self.period

                # Detect if increase
                if fifo.isFull():
                    last = 0
                    increase = False
                    for i in range(len(values)):
                        if last:
                            increase = getattr(values[i], compare)(last)

                            if not increase:
                                break

                            if unit_per_minut and unit_per_minut > abs((values[i] - last) * coeff):
                                increase = False
                                break
                        last = values[i]

                    if increase:
                        return func(name, value)

            self.setReadyCallback(wrapper, name)
            return wrapper
        return decorator

    def detect_increase(self, name, unit_per_minut=None, measure_count=5):
        return self.__detect_increase_or_decrease('__gt__', name, unit_per_minut, measure_count)

    def detect_decrease(self, name, unit_per_minut=None, measure_count=5):
        return self.__detect_increase_or_decrease('__lt__', name, unit_per_minut, measure_count)

    def set_not_in_range(self, name=None):
        def wrapper(func):
            self.setNotInRangeCallback(func, name=None)
            return func
        return wrapper

    def set_ready(self, name=None):
        def wrapper(func):
            self.setReadyCallback(func, name=None)
            return func
        return wrapper

    def set_threshold_callback(self, threshold, name):
        def wrapper(func):
            self.setThresholdCallback(threshold, func, name)
            return func
        return wrapper

