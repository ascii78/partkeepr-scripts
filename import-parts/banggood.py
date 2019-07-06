#!/usr/bin/env python3

# Example banggood csv to partkeepr REST api
# -------------------------------------------
#

import sys
import re
import time
import csv
import json

# for json pretty printing
from pprint import pprint as pp

# http://docs.python-requests.org/en/master/
import requests

# set this to partkeepr settings
HOST = "http://virtualbox"
USER = "admin"
PASS = "admin"

auth = (USER, PASS)

with open('part-small.json') as templatefile:
    template = json.load(templatefile)

with open('banggood.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in reader:

        print(row["description"])

        data = template

        # workaround: https://stackoverflow.com/questions/23120974/python-requests-post-multipart-form-data-without-filename-in-http-request
        r = requests.post('http://virtualbox/api/temp_uploaded_files/upload', files={'url': (None, row["photo-src"])}, auth=auth)

        if r.status_code == 200:
            photo_id = r.json()["image"]["@id"]
        else:
            print("uploading photo went wrong for: ", row["description"])
            sys.exit(1)

        m = re.search('p-([0-9]*).html$', row["url-href"])
        name = m.group(1)

        m = re.search('^https://www.banggood.com/(.*).html', row["url-href"])
        sku = m.group(1)

        data["name"] = name
        data["description"] = row["description"]
        data["distributors"][0]["orderNumber"] = row["orders"]
        data["distributors"][0]["price"] = row["price"]
        data["distributors"][0]["sku"] = sku
        data["stockLevels"][0]["stockLevel"] = row["quantity"]
        data["stockLevels"][0]["price"] = row["price"]
        data["attachments"][0]["@id"] = photo_id

        part = json.dumps(template)
        r = requests.post('http://virtualbox/api/parts', data=part,  auth=auth)
        print(r.status_code, r.json()["name"], r.json()["description"])
        time.sleep(1)
        # input(">>>")
