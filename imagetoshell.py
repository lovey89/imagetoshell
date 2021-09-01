#!/usr/bin/env python3

from PIL import Image
import math
import os
import argparse

PIXEL_WIDTH = 2

ANSI_ESCAPE = '\033['

spaces_can_be_used_with_color = True

parser = argparse.ArgumentParser()
parser.add_argument('image_file', help='foo help')
parser.add_argument('-f', '--full-pixels', action='store_true')
parser.add_argument('-a', '--ansi-colors', action='store_false', dest="true_color")
parser.add_argument('-b', '--bash-output', action='store_true')
parser.add_argument('-g', '--grey-scale', '--gray-scale', action='store_true')
args = parser.parse_args()

image_file = args.image_file
use_full_pixels = args.full_pixels
TRUE_COLOR = args.true_color
bash_output = args.bash_output
grey_scale = args.grey_scale

if bash_output:
    ANSI_ESCAPE = '\\033['

def resize_image_to_screen(im, rows, columns):
    width_multiplier = 0.5 if use_full_pixels else 1.0
    height_multiplier = 0.9 if use_full_pixels else 1.8

    im_width, im_height = im.size

    should_be_resized = False

    w_ratio = int(columns) * width_multiplier / float(im_width)
    h_ratio = (int(rows) * height_multiplier) / float(im_height)

    ratio = min(w_ratio, h_ratio)

    if ratio < 1.0:
        new_height = int(im_height * ratio)
        new_width = int(im_width * ratio)
        #Image.NEAREST (0)
        #Image.LANCZOS (1)
        #Image.BILINEAR (2)
        #Image.BICUBIC (3)
        #Image.BOX (4)
        #Image.HAMMING
        #return im.resize((new_width, new_height), Image.ANTIALIAS)
        #return im.resize((new_width, new_height), Image.LANCZOS)
        return im.resize((new_width, new_height), Image.NEAREST)
    return im

im = Image.open(image_file, 'r').convert('RGBA')
rows, columns = os.popen('stty size', 'r').read().split()

#im = im.resize((basewidth,hsize), Image.ANTIALIAS)
im = resize_image_to_screen(im, rows, columns)

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
    avarage = (r + g + b) / 3
    if true_colors:
        if grey_scale:
            ravarage = round(avarage)
            return f"2;{ravarage};{ravarage};{ravarage}"
        return f"2;{r};{g};{b}"

    elif avarage >= 247.0:
        return "5;231"
    elif avarage <= 5.0:
        return "5;16"
    else:
        grey = round((min(avarage, 242) - 8) / 10) + 232

        if grey_scale:
            return f"5;{grey}"

        ansi = 16 \
            + 36 * color_multiplier(r) \
            + 6 * color_multiplier(g) \
            + color_multiplier(b)

        if (color_diff(r, g, b, ansi) < grey_diff(r, g, b, grey)):
            return f"5;{ansi}"
        else:
            return f"5;{grey}"

def full_px():
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
                    print(f"{ANSI_ESCAPE}0m", end = '')
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
            code = to_terminal_code(r, g, b, TRUE_COLOR)
            if code != last_code:
                print(f"{ANSI_ESCAPE}38;{code}m", end = '')
                last_code = code
            print(fc * PIXEL_WIDTH, end = '')
            # █▓▒░
        print(f"{ANSI_ESCAPE}0m")

def get_alpha(x, y):
    if y < 0:
        return 0
    else:
        return alpha.getpixel((x, y))

def half_px():
    odd = height % 2
    for y in range(0 - odd, height, 2):
        last_fg = None
        last_bg = None
        spaces = 0
        for x in range(0, width):
            au = get_alpha(x, y)
            al = get_alpha(x, y+1)

            if au == 0 and al == 0:
                spaces += 1
                continue
            elif spaces > 0:
                if spaces != x:
                    print(f"{ANSI_ESCAPE}0m", end = '')
                print(" " * spaces, end = '')
                spaces = 0
                last_fg = None
                last_bg = None

            if al == 0:
                fc = "▀"
                if last_bg:
                    print(f"{ANSI_ESCAPE}49m", end = '')
                    last_bg = None
                r = red.getpixel((x,y))
                g = green.getpixel((x,y))
                b = blue.getpixel((x,y))
                code = to_terminal_code(r, g, b, TRUE_COLOR)
                if last_fg != code:
                    print(f"{ANSI_ESCAPE}38;{code}m", end = '')
                    last_fg = code
                print(fc, end = '')
            elif au == 0:
                fc = "▄"
                if last_bg:
                    print(f"{ANSI_ESCAPE}49m", end = '')
                    last_bg = None
                r = red.getpixel((x,y+1))
                g = green.getpixel((x,y+1))
                b = blue.getpixel((x,y+1))
                code = to_terminal_code(r, g, b, TRUE_COLOR)
                if last_fg != code:
                    print(f"{ANSI_ESCAPE}38;{code}m", end = '')
                    last_fg = code
                print(fc, end = '')
            else:
                ru = red.getpixel((x,y))
                gu = green.getpixel((x,y))
                bu = blue.getpixel((x,y))
                rl = red.getpixel((x,y+1))
                gl = green.getpixel((x,y+1))
                bl = blue.getpixel((x,y+1))
                codeu = to_terminal_code(ru, gu, bu, TRUE_COLOR)
                codel = to_terminal_code(rl, gl, bl, TRUE_COLOR)
                if codeu == codel:
                    if last_bg == codeu and spaces_can_be_used_with_color:
                        print(' ', end = '')
                        continue
                    elif last_fg != codeu:
                        print(f"{ANSI_ESCAPE}38;{codeu}m", end = '')
                        last_fg = codeu
                    print('█', end = '')
                elif codeu == last_fg:
                    if last_bg != codel:
                        print(f"{ANSI_ESCAPE}48;{codel}m", end = '')
                        last_bg = codel
                    print('▀', end = '')
                elif codeu == last_bg:
                    print(f"{ANSI_ESCAPE}38;{codel}m", end = '')
                    last_fg = codel
                    print('▄', end = '')
                elif codel == last_fg:
                    print(f"{ANSI_ESCAPE}48;{codeu}m", end = '')
                    last_bg = codeu
                    print('▄', end = '')
                elif codel == last_bg:
                    print(f"{ANSI_ESCAPE}38;{codeu}m", end = '')
                    last_fg = codeu
                    print('▀', end = '')
                else:
                    print(f"{ANSI_ESCAPE}38;{codel}m{ANSI_ESCAPE}48;{codeu}m▄", end = '')
                    last_fg = codel
                    last_bg = codeu
            # █▓▒░
        print(f"{ANSI_ESCAPE}0m")

if bash_output:
    print("#!/bin/bash")
    print('echo -en "\\')

if use_full_pixels:
    full_px()
else:
    half_px()

if bash_output:
    print('"')
