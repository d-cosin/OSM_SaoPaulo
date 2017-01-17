#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from collections import defaultdict
import re

osm_file = open("sao_paulo.osm", "r")

street_type_re = re.compile(r'^\S+\.?', re.IGNORECASE) #regex to match first address word (address type)
street_types = defaultdict(int)
postcode_re = re.compile(r'\d{5}-\d{3}', re.IGNORECASE) #regex to match correct postcodes
problem_postcodes = set([])

def audit_postcode(problem_postcodes, postcode):
    m = postcode_re.match(postcode)
    if not m:
        problem_postcodes.add(postcode)

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        street_types[street_type] += 1

def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v)

def is_postcode(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:postcode")

def is_street_name(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:street")

# correcao do postcode
def correct_postcode(postcode):
    postcode_correct_re = re.compile(r'\d+', re.IGNORECASE) #regex to match only numeric characters in postcode field
    m = postcode_correct_re.findall(postcode)
    return ''.join(m)[:5] + "-" + ''.join(m)[5:]

def audit():
    for event, elem in ET.iterparse(osm_file):
        if is_street_name(elem):
            audit_street_type(street_types, elem.attrib['v'])
        elif is_postcode(elem):
            audit_postcode(problem_postcodes, elem.attrib['v'])
    print_sorted_dict(street_types)
    print problem_postcodes
    print len(problem_postcodes)

    # se precisar, deletar tudo q está em baixo
    for postcode_with_problem in problem_postcodes:
        print correct_postcode(postcode_with_problem)

if __name__ == '__main__':
    audit()
