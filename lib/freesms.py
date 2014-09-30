#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
"""FREE MOBILE SMS NOTIFICATION
 
Send SMS notifications to your cell phone with the Free Mobile's new service.
Enable it on your user account page and get your credentials !
 
Paste this code in a file, import it and invoke the send_sms function
 
>>> import freemobilesmsnotification as sms
>>> sms.send_sms('12345678', 'TopSecretPassword', 'Hello World!')
(True, 'Success')"""

try:
    from urllib import urlencode
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import HTTPError

def send_sms(u, p, m):
    """u : Free Mobile id
   p : Service password
   m : The message

   Returns a boolean and a status string."""

    query = urlencode({'user': u, 'pass': p, 'msg': m})
    url = 'https://smsapi.free-mobile.fr/sendmsg?{}'.format(query)
    errorcodes = {400: 'Missing Parameter',
                  402: 'Spammer!',
                  403: 'Access Denied',
                  500: 'Server Down'}

    try:
        urlopen(url)
        return True, 'Success'

    except HTTPError as e:
        return False, errorcodes[e.code]

def main():
    u, p, m = '12345678', 'TopSecretPassword', 'Hello World !'
    print(send_sms(u, p, m)[1])
    return 0

if __name__ == '__main__':
    main()

