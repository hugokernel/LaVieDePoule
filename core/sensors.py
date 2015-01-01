
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
    PERIOD = 10#60 * 5

    sensors = {}

    '''
    Stored last value with timestamp
    '''
    results = {}

    callbacks_ready = {}
    callbacks_notinrange = {}

    default_validrange = None
    default_type = None

    def __init__(self):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()

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
        self.callbacks_ready[name] = callback

    def setNotInRangeCallback(self, callback, name=None):
        '''
        Callback called when data not in range !
        '''
        self.callbacks_notinrange[name] = callback

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
            if not data:
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
                                self.callbacks_notinrange[key](key, result, validrange)
                        continue

                # Call callback
                for key in (None, name):
                    if key in self.callbacks_ready:
                        self.callbacks_ready[key](name, result)

                # All good ? Save value !
                self.results[name] = (result, time.time())

            time.sleep(self.PERIOD)

    @contextmanager
    def attributes(self, validrange=None, type=None):
        if validrange:
            old_validrange, self.default_validrange = self.default_validrange, validrange
        if type:
            old_type, self.default_type = self.default_type, type
        try:
            yield
        finally:
            if validrange:
                self.default_validrange, validrange = old_validrange, self.default_validrange
            if type:
                self.default_type, type = old_type, self.default_type

