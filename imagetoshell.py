#!/usr/bin/env python3

from PIL import Image

PIXEL_WIDTH = 2

im = Image.open('bowser.png', 'r').convert('RGBA')

width, height = im.size

red, green, blue, alpha = im.split()

for y in range(0, height):
    last_r, last_g, last_b = -1, -1, -1
    spaces = 0
    for x in range(0, width):
        a = alpha.getpixel((x,y))
        if a < 51:
            spaces += 1
            continue
        elif spaces > 0:
            if spaces != x:
                print("\\033[0m", end = '')
            print(" " * PIXEL_WIDTH * spaces, end = '')
            spaces = 0
            last_r, last_g, last_b = -1, -1, -1

        if a < 102:
            fc = "░"
        elif a < 153:
            fc = "▒"
        elif a < 204:
            fc = "▓"
        else:
            fc = "█"

        r = red.getpixel((x,y))
        g = green.getpixel((x,y))
        b = blue.getpixel((x,y))
        if ((r, g, b) != (last_r, last_g, last_b)):
            print(f"\\033[38;2;{r};{g};{b}m", end = '')
            last_r, last_g, last_b = r, g, b
        print(fc * PIXEL_WIDTH, end = '')
        # █▓▒░
    print("\\033[0m")
