#!/usr/bin/env python

#
# test_wifi_basic.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License:   http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Internal unit tests for wireless basic functions
#

import unittest

from kano_wifi_backend import KanoWifi

class TestWifi(unittest.TestCase):
    
    def test_ping(self):
        self.assertEqual(k.ping(), True)

    def test_status(self):
        ssid, ip = k.status()
        self.assertIsNotNone(ssid)
        self.assertIsNotNone(ip)

    def test_scan(self):
        networks = k.scan()

        self.assertTrue(type(networks) == list)
        self.assertTrue(type(networks[0]) == dict)

        self.assertTrue(networks[0].has_key('ssid'))
        self.assertTrue(networks[0].has_key('signal'))
        self.assertTrue(networks[0].has_key('frequency'))
        self.assertTrue(networks[0].has_key('flags'))
        self.assertTrue(networks[0].has_key('bssid'))


if __name__ == '__main__':

    #
    # TODO: Check that pre-requisites are met
    #
    #  * wireless dongle plugged in
    #  * network must be up and running over wireless
    #

    k=KanoWifi(debug=True)
    unittest.main()
