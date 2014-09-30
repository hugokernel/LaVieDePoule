#!/usr/bin/python
import smbus
import re

class adc:

    address = 0x6E

    bus = 0
    channels = [ 0x9C, 0xBC, 0xDC, 0xFC ]

    multiplier = 0.0000386

    def __init__(self):
        # detect i2C port number and assign to i2c_bus
        for line in open('/proc/cpuinfo').readlines():
            m = re.match('(.*?)\s*:\s*(.*)', line)
            if m:
                (name, value) = (m.group(1), m.group(2))
                if name == "Revision":
                    if value [-4:] in ('0002', '0003'):
                        i2c_bus = 0
                    else:
                        i2c_bus = 1
                    break

        self.bus = smbus.SMBus(i2c_bus);

    def getVoltage(self, channel):
        while True:
            data = self.bus.read_i2c_block_data(self.address, self.channels[channel])
            h, m, l, s = data[0:4]
            if not (s & 128):
                break

        # shift bits to product result
        t = ((h & 0b00000001) << 16) | (m << 8) | l
        # check if positive or negative number and invert if needed
        if (h > 128):
            t = ~(0x020000 - t)
        return t * self.multiplier

    def getVoltages(self, channels=[0, 1, 2, 3]):
        out = []
        for channel in channels:
            out.append(self.getVoltage(channel))
        return out

