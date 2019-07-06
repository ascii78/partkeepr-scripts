#!/usr/bin/python3

import os, sys
from pprint import pprint as pp

import requests

HOST="http://localhost"
USER="admin"
PASS="admin"

DELETE=True

headers = {
    'Content-Type': 'application/json',
}

params = (
    ('_dc', '1506284694809'),
    ('itemsPerPage', '9999999'),
    ('columns', '["name"]'),
)

headers = {'Accept': 'text/comma-separated-values'}

auth = (USER, PASS) 

r = requests.get('http://virtualbox/api/part_categories', params=params, headers=headers, auth=auth)

print(r)
print(r.text)

import csv

reader = csv.reader(r.text.splitlines())
for row in reader:
    print('\t'.join(row))

sys.exit(1)

if r.status_code == 200:
    root = r.json()["hydra:member"][0]
    print(root["@id"])
    print(root["name"])

    pp(root)

    # deleting is recursive, no need to delete leaf nodes
    if DELETE:

        toplevels = {}

        for t in root["children"]:
            toplevels[t["name"]] = t["@id"]

        print("toplevels: ", toplevels)

        sys.exit()
        
        for name, id in toplevels.items():
            r = requests.delete(HOST+id, params=params, data="{}", auth=auth)
            if r.status_code == 204:
                print("deleted %s %s" % (name, id))
            else:
                print("NOT deleted %s %s" % (name, id))
                pp(r)

    # send payload with a create request, partkeepr will fill in the null 
    # and false values

    template = """ 
    {    "parentId":null,
         "leaf":false,
         "root":null, 
         "lft":0,
         "rgt":0,
         "lvl":0,
         "name":"%s",
         "description":"",
         "categoryPath":null,
         "parent":"%s",
         "categoryPartKeeprPartBundleEntityParts":[]
    } """ 

    # create categoris based on a textfiles where tabs indicate depth, use a sequence number
    # on toplevel for sorting

    with open("categories.txt") as f:

        seq = 0

        for line in f.readlines():
            name = line.strip("\n")
            count = len(name.split("\t"))
            name = name.strip("\t")

            if count == 1:
                seq += 1
                print("create toplevel in {}: {}".format(root["@id"], name))
                name = "%02d - %s" % (seq, name)
                data = template % (name, root["@id"])
                r = requests.post('http://virtualbox/api/part_categories', params=params, data=data, auth=auth)
                toplevel = r.json()
                print("created: ", toplevel["name"], toplevel["@id"])

            if count == 2:
                print("create midlevel in {}: {}".format(toplevel["@id"], name))
                data = template % (name, toplevel["@id"])
                r = requests.post('http://virtualbox/api/part_categories', params=params, data=data, auth=auth)
                midlevel = r.json()
                print("created: ", midlevel["name"], midlevel["@id"])

            if count == 3:
                print("create endlevel in {}: {}".format(midlevel["@id"], name))
                data = template % (name, midlevel["@id"])
                r = requests.post('http://virtualbox/api/part_categories', params=params, data=data, auth=auth)
                endlevel = r.json()
                print("created: ", endlevel["name"], endlevel["@id"])

else:
    print("Something went wrong with the JSON request")
    sys.exit(1)
