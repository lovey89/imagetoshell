#!/usr/bin/env python3

import sys
import os
from PIL import Image
import math
import argparse

import requests
import re
from io import BytesIO

RESIZE_METHOD = Image.BOX
        #Image.NEAREST (0)
        #Image.LANCZOS (1)
        #Image.BILINEAR (2)
        #Image.BICUBIC (3)
        #Image.BOX (4)
        #Image.HAMMING
        #Image.ANTIALIAS

output = []

PIXEL_WIDTH = 2

ANSI_ESCAPE = '\033['

spaces_can_be_used_with_color = True

parser = argparse.ArgumentParser()
parser.add_argument('image_file', help='foo help')

color_group = parser.add_argument_group("color arguments")
color_group.add_argument('-a', '--ansi-colors', action='store_false', dest="true_color")
color_group.add_argument('-g', '--grey-scale', '--gray-scale', action='store_true')

size_group = parser.add_argument_group("size arguments")
size_group.add_argument('-o', '--original-size', action='store_true')
size_group.add_argument('-r', '--rows', '--height', default=None)
size_group.add_argument('-c', '--columns', '--width', default=None)
size_group.add_argument('-p', '--pixel-art-resize', action='store_true')
size_group.add_argument('-f', '--full-pixels', action='store_true')

output_group = parser.add_argument_group("output arguments")
output_group.add_argument('-b', '--bash-output', action='store_true')

say_group = parser.add_argument_group("say arguments")
say_group.add_argument('-s', '--say', action='store_true')
say_group.add_argument('--say-offset', type=int, default=7)
say_group.add_argument('--say-max-depth', type=int, default=4)
args = parser.parse_args()

image_file = args.image_file
use_full_pixels = args.full_pixels
TRUE_COLOR = args.true_color
bash_output = args.bash_output
grey_scale = args.grey_scale
original_size = args.original_size
requested_height = args.rows
requested_width = args.columns
bubble=args.say
say_offset=args.say_offset
say_depth=args.say_max_depth
RESIZE_METHOD = Image.NEAREST if args.pixel_art_resize else Image.LANCZOS

if len([v for v in [original_size, requested_height, requested_width] if v == True or (v is not None and v != False)]) > 1:
    print("Can only provide one of -o, -r and -c at a time. Exiting..", file = sys.stderr)
    exit(1)

if bash_output:
    ANSI_ESCAPE = '\\033['

def resize_image_to_screen(im, rows, columns):
    width_multiplier = 0.5 if use_full_pixels else 1.0
    height_multiplier = 0.9 if use_full_pixels else 1.8

    im_width, im_height = im.size

    w_ratio = int(columns) * width_multiplier / float(im_width)
    h_ratio = (int(rows) * height_multiplier) / float(im_height)

    ratio = min(w_ratio, h_ratio)

    if ratio < 1.0:
        new_height = int(im_height * ratio)
        new_width = int(im_width * ratio)
        return im.resize((new_width, new_height), RESIZE_METHOD)
    return im

def resize_image(im, rows, columns):
    if rows and columns:
        print("Internal error")
        exit(255)

    im_width, im_height = im.size

    if rows:
        ratio = int(rows) / im_height
    else:
        ratio = int(columns) / im_width

    if ratio < 1.0:
        new_height = int(im_height * ratio)
        new_width = int(im_width * ratio)
        return im.resize((new_width, new_height), RESIZE_METHOD)
    return im

if os.path.isfile(image_file):
    im = Image.open(image_file, 'r').convert('RGBA')
elif re.match("https?://", image_file, re.IGNORECASE):
    url = image_file
    response = requests.get(url)
    im = Image.open(BytesIO(response.content), 'r').convert('RGBA')
else:
    print(f"File '{image_file}' doesn't exist. Exiting...")
    exit(1)

if requested_height or requested_width:
    im = resize_image(im, requested_height, requested_width)
elif not original_size:
    rows, columns = os.popen('stty size', 'r').read().split()
    im = resize_image_to_screen(im, rows, columns)

width, height = im.size

im_data = im.getdata()

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
        row_result = ""
        last_code = ""
        spaces = 0
        for x in range(0, width):
            r, g, b, a = get_pixel(x, y)

            if a < 51:
                spaces += 1
                continue
            elif spaces > 0:
                if spaces != x:
                    row_result += f"{ANSI_ESCAPE}0m"
                row_result += " " * PIXEL_WIDTH * spaces
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

            code = to_terminal_code(r, g, b, TRUE_COLOR)
            if code != last_code:
                row_result += f"{ANSI_ESCAPE}38;{code}m"
                last_code = code
            row_result += fc * PIXEL_WIDTH
            # █▓▒░
        if row_result != "" or output:
            row_result += f"{ANSI_ESCAPE}0m"
            output.append(row_result)

def get_pixel(x, y):
    if y < 0:
        return (0, 0, 0, 0)
    index = y * width + x
    return im_data[index]

def half_px():
    odd = height % 2
    for y in range(0 - odd, height, 2):
        row_result = ""
        last_fg = None
        last_bg = None
        spaces = 0
        for x in range(0, width):
            ru, gu, bu, au = get_pixel(x, y)
            rl, gl, bl, al = get_pixel(x, y+1)

            upper_transparent = au < 51
            lower_transparent = al < 51

            if upper_transparent and lower_transparent:
                spaces += 1
                continue
            elif spaces > 0:
                if spaces != x:
                    row_result += f"{ANSI_ESCAPE}0m"
                row_result += " " * spaces
                spaces = 0
                last_fg = None
                last_bg = None

            if lower_transparent:
                fc = "▀"
                if last_bg:
                    row_result += f"{ANSI_ESCAPE}49m"
                    last_bg = None
                code = to_terminal_code(ru, gu, bu, TRUE_COLOR)
                if last_fg != code:
                    row_result += f"{ANSI_ESCAPE}38;{code}m"
                    last_fg = code
                row_result += fc
            elif upper_transparent:
                fc = "▄"
                if last_bg:
                    row_result += f"{ANSI_ESCAPE}49m"
                    last_bg = None
                code = to_terminal_code(rl, gl, bl, TRUE_COLOR)
                if last_fg != code:
                    row_result += f"{ANSI_ESCAPE}38;{code}m"
                    last_fg = code
                row_result += fc
            else:
                codeu = to_terminal_code(ru, gu, bu, TRUE_COLOR)
                codel = to_terminal_code(rl, gl, bl, TRUE_COLOR)
                if codeu == codel:
                    if last_bg == codeu and spaces_can_be_used_with_color:
                        row_result += ' '
                    elif last_fg == codeu:
                        row_result += '█'
                    elif last_fg == None or not spaces_can_be_used_with_color:
                        row_result += f"{ANSI_ESCAPE}38;{codeu}m"
                        last_fg = codeu
                        row_result += '█'
                    else:
                        row_result += f"{ANSI_ESCAPE}48;{codeu}m"
                        last_bg = codeu
                        row_result += ' '
                elif codeu == last_fg:
                    if last_bg != codel:
                        row_result += f"{ANSI_ESCAPE}48;{codel}m"
                        last_bg = codel
                    row_result += '▀'
                elif codeu == last_bg:
                    row_result += f"{ANSI_ESCAPE}38;{codel}m"
                    last_fg = codel
                    row_result += '▄'
                elif codel == last_fg:
                    row_result += f"{ANSI_ESCAPE}48;{codeu}m"
                    last_bg = codeu
                    row_result += '▄'
                elif codel == last_bg:
                    row_result += f"{ANSI_ESCAPE}38;{codeu}m"
                    last_fg = codeu
                    row_result += '▀'
                else:
                    row_result += f"{ANSI_ESCAPE}38;{codel}m{ANSI_ESCAPE}48;{codeu}m▄"
                    last_fg = codel
                    last_bg = codeu
            # █▓▒░
        if row_result != "" or output:
            row_result += f"{ANSI_ESCAPE}0m"
            output.append(row_result)

if use_full_pixels:
    full_px()
else:
    half_px()

if bubble:
    limit = min(len(output) - 1, say_depth)
    offset = say_offset
    for i, row in enumerate(output):
        if i == limit:
            break

        if row.startswith(" " * (offset + 3 + 2 * i)) and output[i + 1][offset - 1 + 2 * i:offset + 2 + 2 * i] == "   ":
            new_row = " " * (offset + 2 * i) + "\\" + row[(offset + 1 + 2 * i):]
            output[i] = new_row
        else:
            break

if bash_output:
    print("#!/bin/bash")
    print('echo -en "\\')

for row in output:
    print(row)

if bash_output:
    print('"')
