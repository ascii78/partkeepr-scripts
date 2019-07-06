#!/usr/bin/python3

import os, sys
from pprint import pprint as pp

import labels
import requests

from reportlab.graphics import shapes
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth

# set this to partkeepr settings
HOST = "http://localhost"
USER = "admin"
PASS = "admin"

URL  = "http://localhost/api/parts"

auth = (USER, PASS)

def b36enc(integer):
    chars, encoded = '0123456789abcdefghijklmnopqrstuvwxyz', ''

    while integer > 0:
        integer, remainder = divmod(integer, 36)
        encoded = chars[remainder] + encoded

    return encoded

params = (
    ('filter', '[{"subfilters":[],"property":"needsReview","operator":"=","value":true}]'),
)
r = requests.get(URL, params=params, auth=auth)

if r.status_code == 200:

    parts = []

    for p in r.json()["hydra:member"]:
        # pp(p)
        part = {
            "id36": "#" + b36enc(int(p["@id"].replace("/api/parts/", ""))),
            "name": p["name"],
            "description": p["description"],
            "category": p["category"]["name"],
            "location_path": p["storageLocation"]["categoryPath"].replace("Root Category ➤ ", ""),
            "location_name": p["storageLocation"]["name"],
        }
        if len(p["manufacturers"]) >= 1:
            part["1stmanufacturer"] = p["manufacturers"][0]["manufacturer"]["name"]
        else:
            part["1stmanufacturer"] = ""

        parts.append(part)

        print(
            '{id36:<6}|{category:<40}|{name:<20}|{description:<80}|{location_name:<30}|'.format_map(
                part))

else:

    print("Something went wrong with the JSON request")
    sys.exit(1)

# Create an A4 portrait (210mm x 297mm) sheets with 2 columns and 8 rows of
# labels. Each label is 90mm x 25mm with a 2mm rounded corner. The margins are
# automatically calculated.

# Create an A4 portrait (210mm x 297mm) sheet, with an envelope outline in
# the top center part, the envelope is 95mm wide, 145mm long. It's situated
# 2mm from the top and, 59mm from each side (59+145+59~=210mm)
specs = labels.Specification(210, 297, 1, 1, 95, 145, left_margin=59, top_margin=2)

base_path = os.path.dirname(__file__)

# I like this font but it's not distributed with this script, if you have
# a windows install you can find it there or replace this with your own.
registerFont(TTFont('Consolas Bold', os.path.join(base_path, 'Consolas.ttf')))

# Create a function to draw each label. This will be given the ReportLab drawing
# object to draw on, the dimensions (NB. these will be in points, the unit
# ReportLab uses) of the label, and the object to render. Refer to:
# Chapter 11: Graphics of the ReportLab UserGuide
def draw_label(label, width, height, part):
    # The coordinate begins on lower left, use width and height together
    # with fontsize (although in points and not mm) to align the shapes.

    # In partkeepr I'm using a hierarchy exactly similar to
    # http://octopart.com/search, the lines here represent a part with
    # the longest (end node) in that hierarchy. You can use  these as a
    # static test to see if the label is correct

    # label.add(shapes.String(5, height-5, "Clock Generators, PLLs, Frequency Synthesizers", fontName="Consolas Bold", fontSize=10))
    # label.add(shapes.String(10, height-15, "MOSFETs", fontName="Consolas Bold", fontSize=10))
    # label.add(shapes.String(10, height-45, "Lattice Semiconductor", fontName="Consolas Bold", fontSize=13))
    # label.add(shapes.String(10, height-60, "LC4064V-75TN100C", fontName="Consolas Bold", fontSize=13))
    # label.add(shapes.Rect(width-50, height-55, 40, 20, strokeWidth=1, fillColor=None))
    # label.add(shapes.String(width-45, height-48, "#4444", fontName="Consolas Bold", fontSize=11))
    # label.add(shapes.Line(10, height-75, width-10,height-75, strokeWidth=1))

    label.add(shapes.String(10, height - 15, part["category"], fontName="Consolas Bold", fontSize=10))
    label.add(shapes.String(10, height - 45, part["name"], fontName="Consolas Bold", fontSize=13))
    label.add(shapes.String(10, height - 60, part["description"], fontName="Consolas Bold", fontSize=10))
    label.add(shapes.Line(10, height - 75, width - 10, height - 75, strokeWidth=1))
    label.add(shapes.Rect(width - 50, height - 43, 40, 20, strokeWidth=1, fillColor=None))
    label.add(shapes.String(width - 46, height - 36, part["id36"], fontName="Consolas Bold", fontSize=10))
    # moved above the line.
    # label.add(shapes.String(width - 50, height - 110, "ID36", fontName="Consolas Bold", fontSize=8))
    # removed manufacturer
    # label.add(shapes.String(10, height - 115, part["1stmanufacturer"], fontName="Consolas Bold", fontSize=6))

# Create the sheet. Use border to see the outline on an A4 sheet,
# disable for printing on the actual envelopes (due to printer skew)
# sheet = labels.Sheet(specs, draw_label, border=True)
sheet = labels.Sheet(specs, draw_label, border=False)

# Create labels
for part in parts:
    sheet.add_label(part)

sheet.save('labels.pdf')

print("{0:d} label(s) output on {1:d} page(s).".format(sheet.label_count, sheet.page_count))

# if sheet.label_count > 1:
# os.startfile(r'labels.pdf')
