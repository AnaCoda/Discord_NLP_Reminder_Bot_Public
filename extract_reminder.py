import pandas as pd
import numpy as np
import csv
import itertools
import os
import re
import sys
import parsedatetime
from datetime import datetime

def reminderParse(sentence):
    templates = []
    prefixes = ['i have my ', 'i have an ', ' i have a ', 'me that ', ' that the ', 'me to ', 'me of ', 'me for ', 'me about ']
    middles = [' due on ', ' due ', ' on ', ' is due on ', ' should be done by ', ' at ',' by ', ' tomorrow', ' for ', ' next', ' in ']
    
    for prefix in prefixes:
        for middle in middles:
            templates.append({'order': True, 'prefix': prefix, 'middle': middle})
    print("templates loaded")
    parsed = []
    results = extract_from_templates(templates, sentence)
    print("extracting")
    doneSubjects = []
    for subject, time in results:
        print(subject, time)
        newSubject = subject
        for prefix in prefixes:
            newSubject = newSubject.replace(prefix, '')
        if newSubject not in doneSubjects:
            doneSubjects.append(newSubject)
        else:
            continue
        if(len(time) > 0):
            try:
                cal = parsedatetime.Calendar()
                time_struct, parse_status = cal.parse(time)
                time_set=datetime(*time_struct[:6])     #getting the time from the query
                if(parse_status == 1):
                    time_set = time_set.replace(hour=10)
                    time_set = time_set.replace(minute=00)
                    time_set = time_set.replace(second=00)

                parsed.append((newSubject, time_set))
                #print('     SUBJECT: ',newSubject ,' TIME: ',hour,':',mins,':',secs,'on',day,'-',month,'-',year)
            except:
                continue
    return parsed

def load(data, directory):
    with open(data) as f:
        examples = list(csv.reader(f))
    corpus = ""
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename)) as f:
            corpus += f.read().replace("\n", " ")
    return examples, corpus


def find_templates(examples, corpus):
    templates = []
    for a, b in examples:
        templates.extend(match_query(a, b, True, corpus))
        templates.extend(match_query(b, a, False, corpus))

    # Find common middles
    middles = dict()
    for template in templates:
        middle = template["middle"]
        order = template["order"]
        if (middle, order) in middles:
            middles[middle, order].append(template)
        else:
            middles[middle, order] = [template]

    # Look for common prefixes and suffixes
    results = []
    for middle in middles:
        found = set()
        for t1, t2 in itertools.combinations(middles[middle], 2):
            prefix = common_suffix(t1["prefix"], t2["prefix"])
            #suffix = common_prefix(t1["suffix"], t2["suffix"])
            if (prefix) not in found:
                if (not len(prefix) or not prefix.strip()) :
                    continue
                found.add(prefix)
                results.append({
                    "order": middle[1],
                    "prefix": prefix,
                    "middle": middle[0]
                })
    return results


def filter_templates(templates, n):
    return sorted(
        templates,
        key=lambda t: len(t["prefix"]),
        reverse=True
    )[:n]


def extract_from_templates(templates, corpus):
    results = set()
    for template in templates:
        results.update(match_template(template, corpus))
    return results


def match_query(q1, q2, order, corpus):
    q1 = re.escape(q1)
    q2 = re.escape(q2)
    
    regex = f"(.{{0,10}}){q1}((?:(?!{q1}).)*?){q2}(.{{0,10}})"
    results = re.findall(regex, corpus)
    
    return [
        {
            "order": order,
            "prefix": result[0],
            "middle": result[1],
        }
        for result in results
    ]

def find_between(s, start, end):
  return (s.split(start))[1].split(end)[0]

def match_template(template, corpus):
    prefix = re.escape(template["prefix"])
    middle = re.escape(template["middle"])
    suffix = r"(.*)"
    regex = f"{prefix}((?:(?!{prefix}).){{0,100}}?){middle}(.{{0,40}}?)"
    regex = f"{prefix}((?:(?!{prefix}).){{0,100}}?){middle}{suffix}?"
    
    results = re.findall(regex, corpus)
    specialWords = [' tomorrow', ' next ', ' in ']
    for specialWord in specialWords:
        if specialWord in corpus:
            for k, result in enumerate(results):
                if specialWord not in result[1]:
                    newResult = list(result)
                    if newResult[1] != None:
                        newResult[1] = specialWord + newResult[1]
                    else:
                        newResult[1] = specialWord
                    results[k] = tuple(newResult)

    if template["order"]:
        return results
    else:
        return [(b, a) for (a, b) in results]


def common_prefix(*s):
    # https://rosettacode.org/wiki/Longest_common_prefix#Python
    return "".join(
        ch[0] for ch in itertools.takewhile(
            lambda x: min(x) == max(x), zip(*s)
        )
    )


def common_suffix(*s):
    s = [x[::-1] for x in list(s)]
    return common_prefix(*s)[::-1]

