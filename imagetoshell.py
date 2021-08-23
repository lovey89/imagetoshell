#!/usr/bin/env python3

from PIL import Image
import math

PIXEL_WIDTH = 2

im = Image.open('bowser.png', 'r').convert('RGBA')

width, height = im.size

red, green, blue, alpha = im.split()

def color_multiplier(v):
    if v >= 235:
        return 5
    elif v >= 195:
        return 4
    elif v >= 155:
        return 3
    elif v >= 115:
        return 2
    elif v >= 48:
        return 1
    else:
        return 0

def grey_diff(r, g, b, ansi_grey):
    c = (ansi_grey - 232) * 10 + 8
    #return abs(c - r) + abs(c - g) + abs(c - b)
    return math.sqrt((abs(c - r) ** 2 + abs(c - g) ** 2 + abs(c - b) ** 2) / 3)

def color_diff(r, g, b, ansi_color):
    n = ansi_color - 16
    ab = n % 6
    ag = ((n - ab) // 6) % 6
    ar = ((n - ab - ag) // 36) % 6

    ab = ab * 40 + 55 if ab else 0
    ar = ar * 40 + 55 if ar else 0
    ag = ag * 40 + 55 if ag else 0

    #return abs(ar - r) + abs(ag - g) + abs(ab - b)
    return math.sqrt((abs(ar - r) ** 2 + abs(ag - g) ** 2 + abs(ab - b) ** 2) / 3)

def to_terminal_code(r, g, b, true_colors):
    if true_colors:
        return f"\\033[38;2;{r};{g};{b}m"
    elif r >= 247 and g >= 247 and b >= 247:
        return "\\033[38;5;231m"
    elif r <= 5 and g <= 5 and b <= 5:
        return "\\033[38;5;16m"
    else:
        avarage = (r + g + b) / 3
        grey = round((min(avarage, 242) - 8) / 10) + 232

        ansi = 16 \
            + 36 * color_multiplier(r) \
            + 6 * color_multiplier(g) \
            + color_multiplier(b)

        if (color_diff(r, g, b, ansi) < grey_diff(r, g, b, grey)):
            return f"\\033[38;5;{ansi}m"
        else:
            return f"\\033[38;5;{grey}m"

for y in range(0, height):
    last_code = ""
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
            last_code = ""

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
        code = to_terminal_code(r, g, b, False)
        if code != last_code:
            print(code, end = '')
            last_code = code
        print(fc * PIXEL_WIDTH, end = '')
        # █▓▒░
    print("\\033[0m")
