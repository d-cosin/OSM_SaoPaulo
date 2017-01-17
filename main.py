#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from collections import defaultdict
import re

osm_file = open("sao_paulo.osm", "r")

street_type_re = re.compile(r'^\S+\.?', re.IGNORECASE)  #regex to match first address word (address type)
street_types = defaultdict(int)
postcode_re = re.compile(r'\d{5}-\d{3}', re.IGNORECASE)  #regex to match correct postcodes
problem_postcodes = set([])
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

expected = ["Acesso", "Alameda", "Avenida", "Calçadão", "Complexo", "Corredor",
            "Estrada", "Escapatória", "Ladeira", "Largo", "Marginal", "Parque",
            "Passagem", "Pateo", "Praça", "Rodoanel", "Rodovia", "Rua", "Travessa",
            "Via", "Viaduto", "Viela"]

mapping = { "Al.": "Alameda",
            "Av.": "Avenida",
            "Av": "Avenida",
            "avenida": "Avenida",
            "av.": "Avenida",
            "estrada": "Estrada",
            "praça": "Praça",
            "R": "Rua",
            "R.": "Rua",
            "r.": "Rua",
            "RUa": "Rua",
            "RUA": "Rua",
            "rua": "Rua",
            "Rue": "Rua"}

def upadate_postcode(postcode):
    postcode_correct_re = re.compile(r'\d+', re.IGNORECASE)  #regex to match only numeric characters in postcode field
    m = postcode_correct_re.findall(postcode)
    postcode_updated = ''.join(m)[:5] + "-" + ''.join(m)[5:]
    if len(postcode_updated) == 9:
        return postcode_updated
    else:
        print "Invalid postcode lenght {}. Postcode {} will be discarded." .format(len(postcode_updated), postcode)
        return None

def audit_postcode(postcode):
    m = postcode_re.match(postcode)
    if not m:
        postcode = upadate_postcode(postcode)
    return postcode

def update_name(name):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in mapping:
            name = name.split(" ")
            name_correct = ""
            for word in name:
                if word != street_type:
                    name_correct = name_correct + word + " "
                else:
                    name_correct = name_correct + mapping[street_type] + " "
            name = name_correct.strip()
        else:
            print "Street type {} not mapped. Street name will be discarded."\
                  .format(street_type.encode('utf-8'))
            name = None
    return name

def audit_street_type(street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type.encode('utf-8') not in expected:
            street_name = update_name(street_name)
    return street_name

def is_postcode(elem):
    return elem.attrib['k'] == "addr:postcode"

def is_street_name(elem):
    return elem.attrib['k'] == "addr:street"

def parse_top_level(elem):
    node = {}
    created_values = {}
    node["type"] = elem.tag
    pos = [0, 0]
    for key, attrib in elem.attrib.iteritems():
        if problemchars.match(attrib):
            continue
        elif key in CREATED:
            created_values[key] = attrib
        elif key == "lat":
            pos[0] = float(attrib)
        elif key == "lon":
            pos[1] = float(attrib)
        else:
            node[key] = attrib
    if len(pos) > 0 and pos[0] != 0:
        node["pos"] = pos
    node["created"] = created_values
    return node

def shape_element(elem):
    node = {}
    address = {}
    node_refs = []
    if elem.tag == "node" or elem.tag == "way" :
        node = parse_top_level(elem)
        for child in elem:
            if child.tag == "tag":
                if problemchars.match(child.attrib['k']):
                    continue
                elif is_street_name(child):
                    street_name = audit_street_type(child.attrib['v'])
                    if street_name:
                        address["street"] = street_name
                elif is_postcode(child):
                    postcode = audit_postcode(child.attrib['v'])
                    if postcode:
                        address["postcode"] = postcode
                elif child.attrib['k'].startswith("addr:"):
                    adress = {}
                    k_split = child.attrib['k'].split(":")
                    if len(k_split) == 2:
                        address[k_split[1]] = child.attrib['v']
                else:
                    node[child.attrib['k']] = child.attrib['v']
            elif child.tag == "nd":
                node_refs.append(child.attrib['ref'])
        if len(address) > 0:
            node["address"] = address
        if len(node_refs) > 0:
            node["node_refs"] = node_refs
        return node
    else:
        return None

def process_osm():

    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client.master

    data = []
    for event, elem in ET.iterparse(osm_file):
        el = shape_element(elem)
        if el:
            data.append(el)

    db.node.insert(data)


if __name__ == '__main__':
    process_osm()
