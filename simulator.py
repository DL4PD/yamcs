#!/usr/bin/env python3

import binascii
import io
import socket
import sys
from struct import unpack_from
from threading import Thread
from time import sleep


def send_tm(simulator):
    tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with io.open('testdata.ccsds', 'rb') as f:
        simulator.tm_counter = 1
        header = bytearray(8)
        while f.readinto(header) == 8:
            (len,) = unpack_from('>H', header, 6)

            simulator.tm_len = len
            packet = bytearray(len + 14)
            f.seek(-8, io.SEEK_CUR)
            f.readinto(packet)

            tm_socket.sendto(packet, ('127.0.0.1', 10015))
            simulator.tm_counter += 1

            sleep(1)


def receive_tc(simulator):
    tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tc_socket.bind(('127.0.0.1', 10025))
    while True:
        data, _ = tc_socket.recvfrom(4096)
        simulator.last_tc = data
        simulator.tc_counter += 1


class Simulator():

    def __init__(self):
        self.tm_counter = 0
        self.tm_len = 0
        self.tc_counter = 0
        self.tm_thread = None
        self.tc_thread = None
        self.last_tc = None

    def start(self):
        self.tm_thread = Thread(target=send_tm, args=(self,))
        self.tm_thread.daemon = True
        self.tm_thread.start()
        self.tc_thread = Thread(target=receive_tc, args=(self,))
        self.tc_thread.daemon = True
        self.tc_thread.start()

    def print_status(self):
        cmdhex = None
        if self.last_tc:
            cmdhex = binascii.hexlify(self.last_tc).decode('ascii')
        return 'Sent: {} packets size {}. Received: {} commands. Last command: {}'.format(
                         self.tm_counter, self.tm_len, self.tc_counter, cmdhex)


if __name__ == '__main__':
    simulator = Simulator()
    simulator.start()

    try:
        prev_status = None
        while True:
            status = simulator.print_status()
            if status != prev_status:
                sys.stdout.write('\r')
                sys.stdout.write(status)
                sys.stdout.flush()
                prev_status = status
            sleep(0.5)
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.stdout.flush()
