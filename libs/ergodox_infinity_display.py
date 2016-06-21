# !/usr/bin/env python

# Author: Ilia Baranov

import serial
from timeit import timeit
from time import sleep
from math import floor, pow

# Fonts created for ease of Use
from fonts.fonts import *

RED_MASK = 0xFF0000
GREEN_MASK = 0x00FF00
BLUE_MASK = 0x0000FF

# LCD is arranged with 0,0 at lower left corner
# first [] is x direct, second [] is y
lcd = [[0 for x in range(32)] for x in range(128)]

class ErgodoxLCDBuffer(object):
    def __init__(self):
        self.data = [[0 for x in range(32)] for x in range(128)]

    def format_char(self, c, x, y):  # Enter a char at location x,y using small 5x8 font
        for w in range(5):
            if (0 <= x + w <= 132) & (0 <= y + 8 <= 32):  # Boundrary checking
                self.data[x + w][y:y + 8] = list(format(QuickType_5x8[(ord(c) - 32) * 5 + w], '08b'))

    def format_string(self, string, x, y):
        for i, c in enumerate(string):
            self.format_char(c, x + i * 5, y)

    def clear(self):
        for x in range(len(self.data)):
            for y in range(len(self.data[0])):
                self.data[x][y] = 0

class ErgodoxInterface(object):
    def __init__(self, serial):
        self.serial = serial
        self.lcd = ErgodoxLCDBuffer()

# Fairly painless way to do fonts
    def clear(self):  # Clean lcd array and clean screen
        self.lcd.clear()
        self.serial.write("lcdInit \r".encode('ascii'))
        sleep(0.1)

    def lcd_color(self, r, g, b):
        command = "lcdColor " + str(r) + " " + str(g) + " " + str(b) + " \r"
        self.serial.write(command.encode('ascii'))
        sleep(0.05)

    def lcd_hex_color(self, hex_color, bit_width=8):
        offset = 1
        if bit_width == 16:
            offset = 2

        red_mask = pow(RED_MASK, offset)
        green_mask = pow(GREEN_MASK, offset)
        blue_mask = pow(BLUE_MASK, offset)

        red = (hex_color & int(red_mask)) >> (16 * offset)
        green = (hex_color & int(green_mask)) >> (8 * offset)
        blue = (hex_color & int(blue_mask))

        if bit_width == 8:
            red *= red
            green *= green
            blue *= blue

        self.lcd_color(red*red, green*green, blue*blue)

    def send(self):  # Pass an array, for updating the whole screen, slow!
        for segs in range(8):  # have to break into 8 segments of 16 to avoid lcd overload
            for y in range(int(len(self.lcd.data[0]) / 8)):
                command = "lcdDisp " + hex(y) + " " + hex(segs * 16) + " "
                for x in range(int(len(self.lcd.data) / 8)):
                    val = ""
                    for w in range(7, -1, -1):
                        val += str(self.lcd.data[x + segs * 16][y * 8 + w])
                    command += hex(int(val, 2)) + " "
                command += "\r"
                self.serial.write(command.encode('ascii'))
                # print command
                sleep(0.03)  # Fastest I can go before artefacts start to appear

    def invert(self): #invert the display
        self.serial.write("lcdCmd 0xA7\r".encode('ascii'))

    def revert(self): #undo the invert
        self.serial.write("lcdCmd 0xA6\r".encode('ascii'))

    def update_pixel(self, x, y, val):  # Update a single pixel at location x,y, with either 1 or 0
        if (0 <= x <= 132) & (0 <= y <= 32):
            self.lcd.data[x][y] = val;
            ypose = int(floor(y / 8))
            val = ""
            for w in range(7, -1, -1):
                val += str(self.lcd.data[x][ypose * 8 + w])
            command = "lcdDisp " + hex(ypose) + " " + hex(x) + " " + hex(int(val, 2)) + " \r"
            self.serial.write(command.encode('ascii'))
            # print command
            sleep(0.03)

# NOTE: This will update to the upper limit of the Y page stored, as this is actually faster than limiting it to a smaller section
    def send_portion(self, xDims, yDims):  # Update part of the screen, faster for small updates (~30 pixels total)
        for y in range(yDims[0], yDims[1], 2):
            for x in range(xDims[0], xDims[1]):
                if (0 <= x <= 132) & (0 <= y <= 32): self.update_pixel(x, y, self.lcd.data[x][y])

