#!/usr/bin/env python

# test_wifi_connect.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License:   http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Internal unit tests to quickly switch between multiple wireless networks
#

import unittest
import json

from kano_wifi_backend import KanoWifi

try:
    # Create a sample json file with your private networks to test
    with open('test_wifi_connect.json', 'r') as f:
        test_networks=json.load(f)
except:
    test_networks = [
        { 'ssid' : 'network1', 'psk' : 'passphrase1' },
        { 'ssid' : 'network2', 'psk' : 'passphrase2' }
        ]


class TestConnect(unittest.TestCase):
    
    def test_connection(self):

        for network in test_networks:
            connected = k.connect (network['ssid'], network['psk'])
            self.assertTrue(connected, msg='Error connecting to: {}'.format(network['ssid']))


if __name__ == '__main__':

    # TODO: Check that pre-requisites are met
    #
    #  * you need a wireless dongle plugged in
    #  * there must be at least 2 wireless networks in range
    #  * need auth details for both networks
    #

    k=KanoWifi(debug=True)
    unittest.main()
