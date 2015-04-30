#!/usr/bin/python

import re
import sys

declare_line_pattern = '^( *)def +(\w+) *\((.*)'
doc_para_pattern = '^( *)(\w.*):(.*)'
doc_sec_pattern = '^( *)Parameters'
doc_sep_pattern = '^( *)-+'
doc_end_pattern = '^( *)\"\"\"'

record_warning = False

def check_file(path):
    line_no = 0
    in_params_sec = False
    in_dec_sec = False
    finished_func = False
    sep_no = 0
    func_dent = 0

    func = ''
    func_line = 0
    param_str = ''
    
    params_dec = {}
    params_doc = {}

    with open(path,'r') as src:
        for line in src:
            line_no += 1

            if in_dec_sec:
                if ':' in line:
                    in_dec_sec = False
                params_dec.update(get_params_dec(line))

            match_dec = re.match(declare_line_pattern,line)
            if match_dec:
                record_inconsistency(params_dec,params_doc,func_line,path,func)
                param_str = match_dec.group(3)
                if not ':' in param_str:
                    in_dec_sec = True
                func = match_dec.group(2)
                func_line = line_no
                func_dent = len(match_dec.group(1))
                param_str = match_dec.group(3)
                in_params_sec = False
                sep_no = 0
                params_dec = get_params_dec(param_str)
                params_doc = {}

            if not in_params_sec:
                match_sec = re.match(doc_sec_pattern,line)
                if match_sec:
                    in_params_sec = True
                    sep_no = 0
            else:
                match_params = re.match(doc_para_pattern,line)
                if match_params and len(match_params.group(1)) == func_dent + 4:
                    params_doc.update(get_params_doc(line))
                match_sep = re.match(doc_sep_pattern,line)
                if match_sep:
                    sep_no += 1
                    if sep_no > 1:
                        in_params_sec = False
                match_end = re.match(doc_end_pattern,line)
                if match_end:
                    in_params_sec = False
    record_inconsistency(params_dec,params_doc,func_line,path,func)

def get_params_dec(param_str):
    if not param_str:
        return {}

    param_str = param_str.replace(' ','')
    param_str = param_str.replace(')','')
    param_str = param_str.replace(':','')
    params = param_str.split(',')
    ret = {}

    opt_pattern = '(.*)=(.*)'
    for param in params:
        match = re.match(opt_pattern,param)
        if match:
            ret[match.group(1)] = True
        else:
            ret[param] = False
    return ret

def get_params_doc(param_str):
    param_str = param_str.replace(' ','')
    param_pattern = '(.*):(.*)'

    optional = False
    ret = {}

    match = re.match(param_pattern,param_str)
    if match:
        params = match.group(1)
        description = match.group(2)
        if description.find('optional')!=-1:
            optional = True
        for param in params.split(','):
            ret[param] = optional
    return ret

def record_inconsistency(dec,doc,line,filename,funcname):
    dec_set = set(dec)
    doc_set = set(doc)

    if dec_set == doc_set:
        return

    ignore = ['self','args','kwargs']
    dec_set = dec_set - set(ignore)

    undoced = dec_set - doc_set
    if undoced and record_warning:
        warn_str = 'Warning: Undocumented params'
        warn_str += ' in '+str(filename)+':'+str(line)
        warn_str += ':'+str(funcname)+':'
        for param in undoced:
            warn_str += str(param)+' '
        print warn_str

    deprecated = doc_set - dec_set
    if deprecated:
        err_str = 'Error: Deprecated params'
        err_str += ' in '+str(filename)+':'+str(line)
        err_str += ':'+str(funcname)+':'
        for param in deprecated:
            err_str += str(param)+' '
        print err_str

if __name__ == "__main__":
    check_file(sys.argv[1])
