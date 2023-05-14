#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate DCS Corpus Statistics

Created on Fri Apr 14 14:49:38 2023

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import sys
import glob
import json
from collections import Counter, defaultdict

import conllu
from tqdm import tqdm
from indic_transliteration.sanscript import transliterate
import sanskrit_text as skt

###############################################################################

script_dir = os.path.dirname(__file__)
base_dir = os.path.realpath(os.path.join(script_dir, '..', '..'))
data_dir = os.path.join(base_dir, 'data', 'corpus', 'dcs')
stats_dir = os.path.join(data_dir, 'stats')

for required_dir in [data_dir, stats_dir]:
    if not os.path.isdir(required_dir):
        print(f"Required directory `{required_dir}' does not exist.")
        sys.exit(1)

files = glob.glob(f"{data_dir}/*.conllu")

###############################################################################

stats = defaultdict(lambda: defaultdict(Counter))
patterns = defaultdict(Counter)

form_locations = defaultdict(list)

###############################################################################

for file in tqdm(files):
    with open(file) as f:
        content = f.read()
    data = conllu.parse(content)
    for line in data:
        verse_id = line.metadata['sent_counter']
        line_text = transliterate(line.metadata['text'], 'iast', 'devanagari')

        for token in line:
            form = token['form']
            unsandhied = (
                token['misc'].get('Unsandhied')
                if token['misc'] else
                None
            )
            if form:
                form = transliterate(form, 'iast', 'devanagari')
            if unsandhied:
                unsandhied = transliterate(unsandhied, 'iast', 'devanagari')

            if unsandhied and unsandhied != form:
                if form.endswith(skt.ANUSWARA):
                    form_with_ma = (
                        f"{form[:-1]}{skt.AUSHTHYA[-1]}{skt.HALANTA}"
                    )
                    if form_with_ma == unsandhied:
                        modified_form = unsandhied
                else:
                    modified_form = f"{form} ({unsandhied})"
            else:
                modified_form = form

            upos = token['upos']
            feats = token['feats'] if token['feats'] else {}
            stats['upos'][upos].update([modified_form])

            pattern = [f'upos={upos}']
            pattern.extend(f'{k}={v}' for k, v in sorted(feats.items()))
            pattern = '_'.join(pattern)
            patterns[pattern].update([modified_form])

            form_locations[modified_form].append(
                (
                    f"line = {line_text}",
                    f"form={form}, Unsandhied = {unsandhied}",
                    pattern,
                    f"{file.replace('../', '')}, verse = {verse_id}"
                )
            )
            for f, v in feats.items():
                stats[f][v].update([modified_form])

###############################################################################

shown_forms = []
occurrences_data = []
for k, v in stats.items():
    for k1, v1 in v.items():
        occurrences_data.append(f"{k}###{k1}###{v1.most_common(15)}")
        shown_forms.extend([x[0] for x in v1.most_common(15)])

with open(os.path.join(stats_dir, "occurrences.csv"), "w") as f:
    f.write("\n".join(occurrences_data))

for k, v in patterns.items():
    patterns[k] = dict(v.most_common())

with open(os.path.join(stats_dir, "patterns.json"), "w") as f:
    json.dump(patterns, f, ensure_ascii=False, indent=2)

location_data = []
for shown_form in set(shown_forms):
    locations = ["^^".join(x) for x in form_locations[shown_form][:10]]
    location_data.append(
        (shown_form, "^^^^".join(locations))
    )

with open(os.path.join(stats_dir, "locations.csv"), "w") as f:
    f.write("\n".join(["###".join(line) for line in location_data]))

with open(os.path.join(stats_dir, "all_locations.json"), "w") as f:
    json.dump(form_locations, f, ensure_ascii=False, indent=2)

###############################################################################
