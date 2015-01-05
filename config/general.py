# -*- coding: utf8 -*-

FAKE_MODE = True

TWITTER_ON = False

LOW_LIGHT = False

TAKE_PHOTO = False

TWITTER_ACCOUNT = 'LaVieDePoule'
TWITTER_ADMIN_ACCOUNT = 'hugokernel'

'''
Alert config (min, max)
'''
VOLTAGE_ALERT = (10, 12)
CURRENT_ALERT = (0.3, 0.55)
TEMP_ALERT = (3, 32)

'''
One wire sensor id
'''
ONEWIRE_SENSOR0 = '10-0008008ba2a9' # Extérieur
ONEWIRE_SENSOR1 = '10-0008008bceb5' # Nid 1
ONEWIRE_SENSOR2 = '28-0000061496ff' # Nid 2

ONEWIRE_SENSORS = [ ONEWIRE_SENSOR0, ONEWIRE_SENSOR1, ONEWIRE_SENSOR2 ]

'''
Sensor max age
Validity of sensor data
'''
MAX_AGE = 5 * 60

'''
Save to db every x seconds
'''
SAVE_TO_DB_EVERY = 5 * 60

