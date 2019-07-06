#!/usr/bin/env python3

# Example mouser csv to partkeepr REST api
# -------------------------------------------
#

import sys
import time
import csv
import json

# for json pretty printing
from pprint import pprint as pp

# http://docs.python-requests.org/en/master/
import requests

# set this to partkeepr settings
HOST = "http://localhost/api"
USER = "admin"
PASS = "admin"

auth = (USER, PASS)

# upload a file to partkeepr, ie. datasheets, or photos
def upload_file_url(url):
    r = requests.post('%s/temp_uploaded_files/upload' % HOST, files={'url': (None, url)},
                      auth=auth)

    if r.status_code == 200:
        print("uploaded file_url:", url)
        return r.json()["image"]["@id"]
    else:
        print("uploading file_url went wrong for:", url)
        sys.exit(1)

# create a manufacturer
def get_or_create_manufacturer(name):
    params = (
        ('filter', '{"property": "name", "operator": "=", "value": "%s"}' % name),
    )
    r = requests.get('%s/manufacturers' % HOST, params=params, auth=auth)
    if r.status_code != 200:
        print("could not get manufacturer")
        sys.exit(1)
    if r.json()["hydra:totalItems"] == 1:
        print("existing manufacturer", name)
        return r.json()["hydra:member"][0]["@id"]
    else:
        json_out = """
        {"name": "%s", "address": "", "url": "", "email": "", "comment": "", "phone": "", "fax": "",
                    "manufacturerPartKeeprManufacturerBundleEntityManufacturerICLogos": [], "icLogos": [],
                    "manufacturerPartKeeprPartBundleEntityPartManufacturers": []}
        """ % name
        r = requests.post('%s/manufacturers' % HOST, data=json_out, auth=auth)
        print("created manufacturer", name)
        return r.json()["@id"]


# use this template file
with open('part-small.json') as templatefile:
    template = json.load(templatefile)

# use the data we got with chrome webscraper.io extension
with open('mouser.csv', 'r', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in reader:
        data = template
        # pp(row)
        data["name"] = row["Fabrikantnr"]
        data["description"] = row["Omschrijving"].replace(row["categorie"], "").lstrip()
        data["distributors"][0]["distributor"]["@id"] = "/api/distributors/9"
        data["distributors"][0]["orderNumber"] = row["orders"]
        data["distributors"][0]["price"] = row["Toestel"][2:].replace(",", ".")
        data["distributors"][0]["sku"] = row["Mouser-nr"]
        data["stockLevels"][0]["stockLevel"] = row["Aantal"]
        data["stockLevels"][0]["price"] = row["Toestel"][2:].replace(",", ".")

        data["manufacturers"] = [{
            "partNumber": row["Fabrikantnr"],
            "manufacturer": {
                "@id": get_or_create_manufacturer(row["fabrikant"]),
                "@type": "Manufacturer"
            }
        }]

        data["attachments"] = []
        if row["image-src"]:
            data["attachments"].append({
                "@context": "/api/contexts/TempUploadedFile",
                "@type": "TempUploadedFile",
                "@id": upload_file_url(row["image-src"])
            })

        if row["datasheet-href"]:
            data["attachments"].append({
                "@context": "/api/contexts/TempUploadedFile",
                "@type": "TempUploadedFile",
                "@id": upload_file_url(row["datasheet-href"])
            })

        part = json.dumps(template)
        r = requests.post('%s/parts' % URL, data=part, auth=auth)

        if r.status_code == 201:
            print(r.status_code, r.json()["name"], r.json()["description"])
            # input(">>>")
        else:
            print(r.status_code, "ERROR ", r.json()["name"], r.json()["description"])
            input("(ctrl-c to quit / enter to continue) >>>")

        time.sleep(0.4)
