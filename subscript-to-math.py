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

''' 
This script patches rst file(s) subscripted variable notation format from :sub: to :math:
Addition, subtraction, multiplication, equation and abs operands are clustered to single expression.
Division of subscripted variables is converted to :math:'/frac{}{}'

example call:
find . -name '*.rst' | xargs python3 subscript-to-math.py
'''

import argparse
import os
import sys
import re
import glob
import pathlib
import shutil

def patch_sub (matchobj):
    ''' rst substript substitution
   
    Args:
        matchobj - substitution match to substring expresion [re match object]

    Returns:
        s - replacement string :math:'a_sub' [str]
    '''

    s = matchobj.group(0)
    #convert rst :sub: expression to :math
    s = s.replace('`','').replace('\ ','')
    i = s.find(':sub:')
    if i<0: return s
    head = s[:i]
    tail = s[i+5:]
    if len(tail)>1:
        tail = '{'+tail+'}'
    s = ':math:`'+head+'_'+tail+'`'
    return s    

def strip_math (s):
    ''' strips :math:'...' labels from string
    '''
    math_tag = ':math:`'
    while True:
        start = s.find(math_tag)
        if start<0: 
            return s
        stop  = s.find('`',start+len(math_tag))
        if stop<0: 
            return s
        s = s[:start] + s[start+len(math_tag):stop] + s[stop+1:]

def patch_subscript (infile):
    ''' patches rst file subsript notation to :math

    Args:
        infile - path to file [pathlib.Path]
    '''
    sub   = "\w+(\\\\\ )?:sub:`.+?`"  # expresion with subscript
    math  = ":math:`[^`]*`(\\\ )?"
    unit  = "[f|p|n|\u00B5|u|m|k]?[m|V|A|Ω|F|H][\u00B2]?"
    value = "[+-]?[0-9]*[.]?[0-9]*(\s?"+unit+")?"
    valuerng = value + "(\sto\s" + value + ")?"
    bracedmath1 = "(\\\\\|)?"+math+"(\\\ )?(\\\\\|)?"
    bracedmath2 = "[(]?"+math+"(\\\ )?[)]?"
    div_sub = "(\\\\\|)?"+math+'/'+math+"(\\\ )?(\\\\\|)?"              # division of such expresions
    diff_sub = "(\\\\\|)?"+math+'\s?[+–*]+\s'+math+"(\\\ )?(\\\\\|)?"    # other operations
    eq_sub = "(\\\\\|)?"+math+"\s?[=|<|>]\s?"+ value +"(\\\\\|)?"  # equation with numeric
    # include value ranges
    #eq_sub = "(\\\\\|)?"+math+"\s?[=|<|>]\s?"+ valuerng +"(\\\\\|)?"  # equation with numeric
    #eq_exp = math + "(\sto\s" + value + ")"  # equation expanded by range
    outfile = pathlib.Path(str(infile)+'.out')
    with outfile.open('w', encoding='utf-8') as of:
        with infile.open('r', encoding='utf-8') as f:
            for line in f:
                prvline = line
                line = re.sub(sub,patch_sub,line)
                for template in [div_sub, diff_sub, eq_sub, bracedmath1, bracedmath2]:
                    m = re.search(template, line) 
                    if m is not None:
                        patch = m.group(0)
                        br = ['','']
                        if patch.startswith('\|') and patch.endswith('\|'):
                            patch = patch[2:-2]
                            br=['|','|']
                        if patch.startswith('(') and patch.endswith(')'):
                            patch = patch[1:-1]
                            br=['(',')']
                        patch = patch.replace('\ :sup:`2`','^2')
                        patch = patch.replace('\ ','').strip()
                        patch = patch.replace('to',' to ').strip()
                        patch = strip_math(patch)
                        if template == div_sub:
                            patch = ':math:`' +br[0]+ '\\frac{' + patch.replace('/','}{') + '}' +br[1]+ '`'
                        else:
                            patch = ':math:`' +br[0]+ patch +br[1]+ '`'
                        i = line.find(m.group(0))
                        if i>0 and line[i-1]!=' ':
                            patch = '\ '+patch
                        i += len(m.group(0))
                        #if not ( line[i:].startswith(' ') or line[i:].startswith('\ ') ):
                        if not line[i] in [' ','\\','\n']: 
                            patch += '\ '
                        line = line.replace(m.group(0),patch)
                        
                of.write (line)
    shutil.move(outfile,infile) # overwrite old file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "files",
            help="Files to be patched",
            type=pathlib.Path,
            nargs='+')

    args = parser.parse_args()
    files = [f.resolve() for f in args.files]
    for f in files:
        print (f'Patching {str(f)}')
        patch_subscript (f)


if __name__ == "__main__":
    sys.exit(main())

