#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 SkyWater PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import print_function

import csv
import os
import re
import pyparsing as pp
import shutil

'''
This script appends 5th,'Unit' column to periphery rules in perphery.csv
Units are assumed based on rule description and value fields.
The rules with empty value field are assigned empty unit field.
The units are assigned based on keywords in description or mentions in description,
using following logic:
Keyword in 2 first description words > mentions > keywords anywhere in description.
Unit mentions can match any of defined unit aliases.
Keywords and aliases are defined in pick_units.
Description is filtered: aliases replaced with uniform unit notation,
trailing [unit] removed.

example call:
cd docs/rules/periphery
python3 ./periphery-append-units-to-csv.py
'''



def pick_units (rdesc, rvalue):
    """Picks rule unit based on rule description and value
       Units are detected by presence of any alias or by keyword guess.
       Optionally, keyword within first 2 words can override unit alias found (strong guess).
       Description is filtered: unit aliases are unified, trailing '[unit]' removed.

    Args:
        rdesc: str
            rule description
        rvlue: str
            rule value


    Returns:
        unit : str
            rule unit
        desc: str
            filtered rule description
    """
    mu = '\u00B5'
    sq = '\u00B2'
    no_unit_values = { # values which imply no unit
        'N/A':'N/A',
        '':'',
        }
    desc_picks = {  # recognized units and their aliases
        'deg'     :['degrees','deg','[deg]','(deg)'],
        'mm'      :['mm','[mm]','(mm)'],
        'mm'+sq   :['mm2','[mm2]','(mm2)','mm^2','[mm^2]','(mm^2)','mmsq'],
        mu+'m'    :['um','[um]','(um)'],
        mu+'m'+sq :['um2','[um2]','(um2)','um^2','[um^2]','(um^2)','umsq'],
        'nm'  :['nm','[nm]','(nm)'],
        }
    guess_keywords = { # keywords related to units
        'deg'     :['angle','angles'],
        mu+'m'    :['length','width','space','spacing','distance','enclosure','enclosed','step','l','w','differ','size','within'],
        mu+'m'+sq :['area'],
        '\-'      :['density']
    }
    allow_guessing     = True # allow guessing unit from keywords
    strong_guess_limit = 2    # keyword guess within first n words trumps found unit alias. 0 - disable.

    if rvalue in no_unit_values:
        return no_unit_values[rvalue],rdesc
    unit = []
    # search desc for unit aliases
    desc_search = re.split(' |_|,|\.|\:|\n|\||"',rdesc)
    for u in desc_picks:
        for alias in desc_picks[u]:
            if alias in desc_search:
                unit.append(u)
                if alias == desc_search[-1]: # remove alias if last word od descrition
                    rdesc = rdesc.replace(alias,'')
                else:                        # otherwise replace with unified unit
                    rdesc = rdesc.replace(alias,u)
    # guess unit from description
    if allow_guessing:
        desc_search = [x.lower() for x in desc_search]
        for u in guess_keywords:
            for k in guess_keywords[u]:
                # strong guess: override if keyowrd in first n words and no similar unit found:
                if k in desc_search[:strong_guess_limit] and not u[1:] in [x[1:] for x in unit]:
                    unit = [u]
                # regular guess: use keywords if no unit found yet
                if not len(unit) and k in desc_search:
                    unit = [u]
    # if more units than one, remove duplicates and join
    unit = " ".join(list(dict.fromkeys(unit)))
    #print ([unit, unit[1:]])
    return unit, rdesc

def append_units_to_periphery_csv (infile):
    """Parses common perihery rule csv file and appends unit column if not present yet
       Units are picked based on description and value by pick_units() function
       Input file is overwritten.

    Args:
        infile: str
            common periphery rule csv file (periphery.csv)

    Returns:
        None
    """

    DescColumnNo = 1 # description column (from 0)
    ValColumnNo  = 3 # value column
    UnitColumnNo = 4 # unit column

    outfile = infile+'.tmp'
    with open (outfile,'w', newline='', encoding='utf8') as of:
        for l in open(infile, encoding='utf8'):
            if '.-)' in l or l.startswith('Note:'):
                of.write(l)
                continue
            lcopy = l.replace('…','\...')
            fields=pp.commaSeparatedList.parseString(lcopy).asList()
            if fields[0] == '':
                fields[0] = l.partition(',')[0]
            fields = [f.replace('\...','…') for f in fields]
            if (len(fields)!=UnitColumnNo    or
                fields[0].endswith('Errors') or
                fields[0] in ['','\n','Rule']):
                  of.write(l)
                  continue
            desc = fields [DescColumnNo]
            val  = fields [ValColumnNo]
            unit,d = pick_units (desc, val)
            fields [DescColumnNo] = d
            fields.append(unit)
            of.write(','.join(fields)+'\n')
    shutil.move(outfile,infile) # overwrite old file



if __name__ == "__main__":
    append_units_to_periphery_csv('periphery.csv')



