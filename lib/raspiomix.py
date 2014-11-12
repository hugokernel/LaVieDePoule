#!/usr/bin/python

class Raspiomix_Base:

    '''
    RaspiOMix version 1.0.1
    IO0 = 7
    IO1 = 11
    IO2 = 13
    IO3 = 15

    DIP0 = 12
    DIP1 = 16
    '''

    '''
    RaspiOMix version 1.1.0
    '''

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

class Raspiomix(Raspiomix_Base):

    i2c = None
    i2c_bus = 0

    ADC_MULTIPLIER = 0.0000386

    def __init__(self):
        import re
        import smbus

        # detect i2C port number and assign to i2c_bus
        for line in open('/proc/cpuinfo').readlines():
            m = re.match('(.*?)\s*:\s*(.*)', line)
            if m:
                (name, value) = (m.group(1), m.group(2))
                if name == "Revision":
                    if value [-4:] in ('0002', '0003'):
                        self.i2c_bus = 0
                    else:
                        self.i2c_bus = 1
                    break

        self.i2c = smbus.SMBus(self.i2c_bus);

    def readAdc(self, channels=(0, 1, 2, 3)):
        '''
        Read analog channel
        '''

        def format(h, m, l):
            # shift bits to product result
            t = ((h & 0b00000001) << 16) | (m << 8) | l
            # check if positive or negative number and invert if needed
            if (h > 128):
                t = ~(0x020000 - t)
            return t * self.ADC_MULTIPLIER

        out = []
        for channel in ((channels,) if type(channels) == int else channels):
            while True:
                data = self.i2c.read_i2c_block_data(self.I2C_ADC_ADDRESS, self.ADC_CHANNELS[channel])
                h, m, l, s = data[0:4]
                if not (s & 128):
                    break

            out.append(format(h, m, l))

        return out[0] if type(channels) == int else out

    def readRtc(self):
        '''
        Read rtc clock
        '''

        try:
            data = self.i2c.read_i2c_block_data(self.I2C_RTC_ADDRESS, 0x00)
        except IOError as e:
            raise IOError(str(e) + " (Maybe rtc_ds1307 module is loaded ?)")

        def bcd_to_int(bcd):
            """
            2x4bit BCD to integer
            """
            out = 0
            for d in (bcd >> 4, bcd):
                for p in (1, 2, 4 ,8):
                    if d & 1:
                        out += p
                    d >>= 1
                out *= 10
            return out / 10

        data[0] = bcd_to_int(data[0])
        data[1] = bcd_to_int(data[1])

        d = (data[2])
        if (d == 0x64):
            d = 0x40
        data[2] = bcd_to_int(d & 0x3F)

        for i, item in enumerate(data[3:7]):
            data[i + 3] = bcd_to_int(item)

        return '20%02d-%02d-%02dT%02d:%02d:%02d' % (data[6], data[5], data[4], data[2], data[1], data[0])

if __name__ == '__main__':
    r = Raspiomix()
    print(r.readRtc())
    print(r.readAdc(0))
    print(r.readAdc((0, 1, 2, 3)))

