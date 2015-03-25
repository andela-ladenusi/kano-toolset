#!/usr/bin/python

# kano_wifi_backend.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License:   http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Provides a simple interface to quickly scan and switch wireless networks
#

import os
import time
import sys
import pexpect
from subprocess import Popen, PIPE, STDOUT

from kano.utils import run_cmd


class KanoWifi:
    '''
    KanoWifi encapsulates access to the WPA Supplicant daemon
    via the WPA_Cli command line tool. This allows for easy access
    to basic common functions: status, scan and connect.
    '''

    def __init__(self, wlan_iface='wlan0', init=True, debug=False):
        self.wpacli='/sbin/wpa_cli'
        self.debug=debug
        self.iface=wlan_iface

        # Init makes sure the supplicant daemon is up and ready
        if init:
            if not self.ping():
                raise IOError('WPA Supplicant is not ready')

            if not self.set_interface(wlan_iface):
                raise IOError('Wireless device {} not found'.format(wlan_iface))

    def _send_command_(self, cmd, ack=None):
        '''
        Sends a command to wpa_cli and return the response in a list of strings.
        For asynchronous commands, set ack to the expected response.
        '''
        data = None
        if self.debug:
            print '>> sending command: {} ack: {}'.format(cmd, ack)

        if ack:
            # asynchronous command
            wpa=self._connect_wpacli_()
            wpa.sendline(cmd)
            try:
                wpa.expect(ack)
                wpa.close()
                data=ack
            except:
                pass
        else:
            try:
                data = os.popen('{} {}'.format(self.wpacli, cmd)).read().splitlines()
            except:
                pass

        if self.debug:
            print '>> command response: {}'.format(data)

        return data

    def _connect_wpacli_(self):
        '''
        Start wpa_cli and return a pexpect object to interact with.
        Use this form instead of _send_command_ if you need to chain multiple operations
        '''
        wpa_cli = pexpect.spawn('wpa_cli')
        try:
            wpa_cli.expect('\n>')
        except:
            raise IOError('WPA Supplicant is not ready')

        return wpa_cli

    def ping(self):
        '''
        Returns True if the supplicant daemon is ready to attend us
        '''
        pong='PONG'
        if self._send_command_('ping', ack=pong) == pong:
            return True

        return False

    def set_interface(self, wlan_iface):
        '''
        Sets the wireless interface to operate on (wlan0, 1, ...)
        '''
        if self._send_command_('interface {}'.format(wlan_iface), ack=wlan_iface) == wlan_iface:
            return True

        return False

    def status(self):
        '''
        Returns the current ssid and ip to which wireless device is associated
        TODO: More testing when not associated to any network
        '''
        ssid=ip=None
        data = self._send_command_('status')
        for line in data:
            try:
                key, value = line.split('=')
                if key=='ssid': ssid=value
                if key=='ip_address': ip=value
            except:
                pass

        return ssid, ip

    def scan(self):
        '''
        Performs a network scan and returns a list of dictionaries
        explaining which wireless networks are in range
        '''
        networks=[]

        # request an asynchronous scan
        if not self._send_command_('scan', ack='CTRL-EVENT-SCAN-RESULTS'):
            return networks
        
        # parse the response to create a list of networks
        wpa=self._connect_wpacli_()
        data = self._send_command_('scan_results')
        for line in data:
            if line.find('\t') != -1:
                bssid, frequency, signal, flags, ssid = line.split('\t')

                # WARNING: multiple ssids with differing bssids would be included
                networks.append ( { 'bssid' : bssid, 'frequency' : frequency,
                                    'signal' : signal, 'flags' : flags,
                                    'ssid' : ssid } )

        return networks

    def connect(self, ssid, passphrase):
        '''
        Connect to the specified ssid network using passphrase.
        If the device is currently associated, it will automatically switch away.
        Returns True if connection was successful and a new IP is ready.
        '''

        # We start and stop the DHCP client our way
        udhcpc_cmdline='udhcpc -S -t 70 -A 20 -n -a ' \
            '--script=/etc/udhcpc/kano.script -i {}'.format(self.iface)

        # Obtain a pexpect object to wpa_cli to chain multiple commands
        wpa = self._connect_wpacli_()

        if self.debug:
            # wpa_cli progress messages will go to the console
            wpa.logfile=sys.stdout

        # Tell WPA Supplicant to add a new network
        wpa.sendline('add_network')
        wpa.expect('\r\n([0-9]+)')
        network_id = wpa.match.group(1)

        # Set the new network parameters
        wpa.sendline('set_network {0} ssid "{1}"'.format(network_id, ssid))
        wpa.expect('OK')

        wpa.sendline('set_network {0} psk "{1}"'.format(network_id, passphrase))
        wpa.expect('OK')

        wpa.sendline('enable_network {0}"'.format(network_id))
        wpa.expect('OK')

        # This command will trigger an association asynchronously
        wpa.sendline('select_network {0}"'.format(network_id))
        try:
            wpa.expect('OK')
            wpa.expect('CTRL-EVENT-CONNECTED')
        except:
            # Timeout: most commonly wrong passhprase, out of range
            return None

        # restart the dhcpc server now, wpa supplicant will keep an eye on this
        # to decide if the link is ok, falling back to not associated otherwise
        run_cmd ('pkill -f "{}"'.format(udhcpc_cmdline))
        run_cmd ('{}'.format(udhcpc_cmdline))

        # return the ssid and assigned IP address
        return self.status()
