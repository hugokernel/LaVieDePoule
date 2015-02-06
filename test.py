
import sys

class X(object):
    data = []

    def __init__(self):
        self.data = []

    def __call__(self):
        print('here')

    def __lt__(self, other):
        #print('::', sys._getframe().f_code.co_name)
        self.data.append(('__lt__', other))
        return self

    def __gt__(self, other):
        self.data.append(('__gt__', other))
        return self

    def __add__(self, other):
        print('PAF', other)
        self.data.append(('__add__', other))
        return self

    def __and__(self, other):
        self.data.append(('__and__', other))
        return self

    def __or__(self, other):
        self.data.append(('__or__', other))
        return self

    def __eq__(self, other):
        self.data.append(('__eq__', other))
        return self

    def ___repr__(self):
        out = []
        for op, val in self.data:
            out.append('x %s %s' % (op, val))
        return ' and '.join(out)

    def __cmp__(self, other):
        print('--')

    #def __getattr__(self, name):
    #    print(name + ' doesn\'t exists !')

    #def __getattribute__(self, name):
    #    print(name + ' doesn\'t exists !')

    #def __setattr__(self, name, value):
    #    print(name + ' doesn\'t exists !', value)

    def test(self, value):
        print('dump', self.data)
        for op, val in self.data:
            func = getattr(value, op)
            print('?:', value, op, val, func(val))
            status = func(val)
            continue
            if not func(val):
                status = False
                continue
                print('no:', value, op, val)
                return False

        print('status:', status)
        return True

'''
temp = X()
current = X()
voltage = X()

#print(0<temp)
#print((0<current<10) or (20<current<30))
#print(voltage<10)

#(0<current<10) + (20<current<30)
(0<current<10) + (current<30)
#print(current)
r = current.test(19)

#r = 0<voltage
#print(r)

#voltage>12
#print(voltage)

sensor.threshold(limit=(1, 10))
sensor.threshold(validvalue=1)
'''

from core import dialog
from core.speak import speak

s = speak(dialog.eggs_detected, count=2)
print(s)

