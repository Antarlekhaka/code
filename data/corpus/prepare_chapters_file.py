#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare Chapter File

@author: Hrishikesh Terdalkar
"""

###############################################################################

import re
import os
import csv
import glob

###############################################################################

CORPUS_ID = 1
FILES = sorted(glob.glob("dcs/*.conllu"))

KANDA = {
    "Bā": "Bāla",
    "Ay": "Ayodhyā",
    "Ār": "Āraṇya",
    "Ki": "Kiṣkindhā",
    "Su": "Sundara",
    "Yu": "Yuddha",
    "Utt": "Uttara"
}

###############################################################################

CSV_DATA = []
for filename in FILES:
    filepath = os.path.realpath(filename)
    pattern = r"Rāmāyaṇa-([0-9]+)-Rām, ([^,]+), ([0-9]+)-([0-9]+).conllu"
    m = re.match(pattern, os.path.basename(filepath), flags=re.DOTALL)
    if m:
        corpus_id = CORPUS_ID
        kanda_short = m.group(2)
        kanda_sarga_id = m.group(3)
        chapter_dcs_id = m.group(4)

        if os.path.isfile(
            filepath
            .replace("dcs/", "dcs/split/")
            .replace(".conllu", "-1.conllu")
        ):
            split_files = sorted(glob.glob(
                filepath
                .replace("dcs/", "dcs/split/")
                .replace(".conllu", "-[0-9]*.conllu")
            ))
            for idx, split_filepath in enumerate(split_files, start=1):
                chapter_name = (
                    f"{KANDA[kanda_short]} {kanda_sarga_id} (part {idx})"
                )
                chapter_description = f"DCS (chapter_id = {chapter_dcs_id})"

                CSV_DATA.append([
                    corpus_id,
                    chapter_name,
                    chapter_description,
                    split_filepath
                ])
        else:
            chapter_name = f"{KANDA[kanda_short]} {kanda_sarga_id}"
            chapter_description = f"DCS (chapter_id = {chapter_dcs_id})"

            CSV_DATA.append([
                corpus_id,
                chapter_name,
                chapter_description,
                filepath
            ])

with open("chapters.csv", encoding="utf-8", mode="w") as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(CSV_DATA)