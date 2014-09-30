
# -*- coding: utf8 -*-

import random

'''

    Step 0: Start from here
    (
        '{0} {1}',
        (
            ( 5, 'Bonjour {0}', (
                ( 1, 'toi !' ),
                ( 1, 'vous {0}', (
                    ( '!', ),
                    ( '?', )
                )),
            )),
            ( 2, 'Salut' ),
        ),
        (
            ( 1, 'Blaireau!' ),
            ( 2, 'Bolos!' ),
        )
    )

    Step 1: Random data and extract

    (
        ( 'Bonjour {0}', (
            ( 'vous {0}', (
                ( '!', ),
            )),
        )),
        ( 'Bolos!' ),
    )

    Step 2: Resolve path

    (
        'Bonjour {0}', 'vous {0}', '!'
        'Bolos!'
    )

    Step 4: Resolve all array

    (
        'Bonjour vous !',
        'Bolos'
    )

    Step 5: Create string

    '{0} {1}' % ('Bonjour vous !', 'Bolos')

'''

def speak(data, **kwargs):
    out = []
    string = ''

    def render(data, out=[], startat=1):
        line = []
        for items in data[startat:]:
            assert(type(items) is tuple)
            assert(0 < len(items) < 4)
            if len(items) == 1:
                weight, item = 1, items[0]
            elif len(items) == 2:
                weight, item = items
                payload = None
            elif len(items) == 3:
                weight, item, payload = items

            for w in range(0, weight):
                line.append(items)

        random.shuffle(line)
        if len(line[0]) > 2:
            _, item, payload = line[0]
            out.append(line[0][1])
            render(payload, startat=0)
        elif len(line[0]) == 2:
            weight, item = line[0]
            out.append(item)
        elif len(line[0]) == 1:
            out.append(line[0][0])

        return out

    def format(data):
        out = ''
        params = []
        for e in data[::-1]:
            if '{' in e:
                params = [ e.format(*params) ]
                out = ''.join(params)
            else:
                params.append(e)
        return out

    for items in data[1:]:
        try:
            render.func_defaults[0][:] = []
        except AttributeError:
            render.__defaults__[0][:] = []

        t = render(items, startat=0)
        string = format(t) if len(t) > 1 else t[0]
        out.append(string)

    string = data[0].format(*out)

    # Replace argument
    for key, value in list(kwargs.items()):
        string = string.replace('%' + key + '%', value)

    return string

if __name__ == '__main__':

    test = (
        '{0} {1}',
        (
            ( 5, 'Bonjour {0}', (
                ( 1, 'toi !' ),
                ( 1, 'vous {0}', (
                    ( '!', ),
                    ( '?', )
                )),
                ( 3, 'il est %datetime%' )
            )),
            ( 2, 'Salut' ),
        ),
        (
            ( 1, 'Coucou !' ),
            ( 2, 'Hello {0}', (
                ( 5, 'à vous {0} !', (
                    ( 'l\'inconnu', ),
                    ( 'la personne', )
                )),
                ( 4, 'guys' )
            )),
        )
    )

    print(speak(test, datetime='2014-08-19 09:03:35'))

