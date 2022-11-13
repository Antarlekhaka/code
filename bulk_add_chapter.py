#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add chapters in bulk

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import csv

from flask import Flask

# Local
from settings import app
from models_sqla import db

from utils.database import add_chapter
from utils.conllu import DigitalCorpusSanskrit

###############################################################################

webapp = Flask(__name__)
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}
db.init_app(webapp)
webapp.app_context().push()

###############################################################################

DCS = DigitalCorpusSanskrit()

###############################################################################


def bulk_add_chapters(chapters_file):
    """Add chapters in bulk

    Parameters
    ----------
    chapters_file : str
        Path to CSV file containing chapter details
    """
    with open(chapters_file, encoding="utf-8") as f:
        csvreader = csv.reader(f)
        chapters_data = list(csvreader)

    for chapter_data in chapters_data:
        corpus_id = int(chapter_data[0].strip())
        chapter_name = chapter_data[1].strip()
        chapter_description = chapter_data[2].strip()

        chapter_file = chapter_data[3].strip()

        if not os.path.isfile(chapter_file):
            print(f"No file {chapter_file}")
            continue

        with open(chapter_file, encoding="utf-8") as f:
            chapter_content = f.read()
        chapter_data = DCS.read_conllu_data(chapter_content)
        result = add_chapter(
            corpus_id=corpus_id,
            chapter_name=chapter_name,
            chapter_description=chapter_description,
            chapter_data=chapter_data
        )


###############################################################################
