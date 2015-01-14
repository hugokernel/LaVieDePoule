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
ONEWIRE_SENSOR0 = '28-000006a093e4' # Nid 2
ONEWIRE_SENSOR1 = '28-000006a087ef' # Nid 1
ONEWIRE_SENSOR2 = '28-0000061496ff' # Extérieur

ONEWIRE_SENSORS = [ ONEWIRE_SENSOR0, ONEWIRE_SENSOR1, ONEWIRE_SENSOR2 ]

'''
Sensor max age
Validity of sensor data
'''
MAX_AGE = 5 * 60

'''
Save to db every x seconds
'''
SAVE_TO_DB_EVERY = 60

'''
Web server
'''
SERVER_ON = True

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5678

