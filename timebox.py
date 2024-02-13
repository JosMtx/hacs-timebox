import sys
import socket
from PIL import Image
from itertools import product
import logging
import os

_LOGGER = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

class Timebox:
    def __init__(self, mac, debug=False):
        self.debug = debug
        self.mac = mac

    def connect(self):
        # open socket on channel 4
        if(self.debug):
            _LOGGER.info('Connecting to ' + self.mac + ' on channel 4')
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.sock.settimeout(10)
        try:
            self.sock.connect((self.mac, 4))
            # read HELLO
            ret = self.sock.recv(256)
            if(self.debug):
                _LOGGER.info('<- ' + ''.join('{:02x} '.format(x) for x in ret))
        except Exception as e:
            _LOGGER.error(e)
            return False
            
        return True

    def disconnect(self):
        self.sock.close()

    def send_raw(self, payload):
        paylist = list(payload)
        # compute size, presented as two bytes LSB first
        size = len(paylist) + 2 # size includes checksum
        content = [size & 0xff, size >> 8]
        content += paylist
        # compute checksum on unescaped content (inclusing size)
        ck1, ck2 = self.checksum(content)
        content += [ck1, ck2]
        # escape full content (size + payload + checksum) and add start and end markers
        content = bytearray([0x01] + self.escape(content) + [0x02])
        if (self.debug):
            _LOGGER.info('-> ' + ''.join('{:02x} '.format(x) for x in content))
        self.sock.send(content)
        # read response, requied to avoid filling buffer, we could also check return code
        ret = self.sock.recv(256)
        if(self.debug):
            _LOGGER.info('<- ' + ''.join('{:02x} '.format(x) for x in ret))
            
    # escape "unauthorized" byte values (0x01 and 0x02)
    def escape(self, bytes):
        _bytes = []
        for b in bytes:
            if (b == 0x01):
                _bytes += [0x03, 0x04]
            elif (b == 0x02):
                _bytes += [0x03, 0x05]
            elif (b == 0x03):
                _bytes += [0x03, 0x06]
            else:
                _bytes += [b]
        return _bytes

    # checksum is a simple byte sum, returned as two bytes LSB first
    def checksum(self, bytes):
        ck = sum(bytes)
        return ck & 0xff, ck >> 8
        
    def load_image(self, file):
        with Image.open(file).convert("RGBA") as imagedata:
            return self.process_image(imagedata)

    def process_image(self, source):
        img = [0]
        first = True

        for c in product(range(11), range(11)):
            y, x = c
            r, g, b, a = source.getpixel((x, y))
            if (first):
                img[-1] = ((r & 0xf0) >> 4) + (g & 0xf0) if a > 32 else 0
                img.append((b & 0xf0) >> 4) if a > 32 else img.append(0)
                first = False
            else:
                img[-1] += (r & 0xf0) if a > 32 else 0
                img.append(((g & 0xf0) >> 4) + (b & 0xf0)) if a > 32 else img.append(0)
                img.append(0)
                first = True
        return img

    def send_image(self, img):
        self.send_raw([0x44, 0x00, 0x0A, 0x0A, 0x04] + img)

    def show_time(self):
        self.send_raw([0x45, 0x00, 0x01]) # 24h format
        
    def show_weather(self):
        self.send_raw([0x45, 0x01, 0x00]) # Celsius
        
    def show_image(self, name):
        img = self.load_image(dir_path + '/images/' + name + '.png')
        self.send_image(img)

    def set_volume(self, vol):
        self.send_raw([0x08, vol])
        
    def set_brightness(self, bright):
        self.send_raw([0x74, bright])
