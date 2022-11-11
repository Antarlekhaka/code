#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCS CoNLL-U Parsing Utility

@author: Hrishikesh Terdalkar
"""

from pathlib import Path

import conllu

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

###############################################################################


def parse_int(text: str) -> int or None:
    try:
        return int(float(text.strip()))
    except Exception:
        pass


###############################################################################


class DigitalCorpusSanskrit:
    INTERNAL_SCHEME = sanscript.IAST
    FIELDS = [
        "id",      # 01
        "form",    # 02 word form or punctuation symbol
        # if it contains multiple words, the annotation
        # follows the proposals for multiword annotation
        # (URL: format.html#words-tokens-and-empty-nodes)
        "lemma",   # 03 lemma or stem, lexical id of lemma is in column 11
        "upos",    # 04 universal POS tags
        "xpos",    # 05 language specific POS tags, described in `pos.csv`
        "feats",   # 06
        "head",    # 07
        "deprel",  # 08
        "deps",    # 09
        "misc"     # 10
        # Misc Fields
        # LemmaId: matches first column of `dictionary.csv`
        # OccId: id of this occurence of the word
        # Unsandhied: Unsandhied word form (padapāṭha version)
        # WordSem: Ids of word semantic concepts, matches first column of
        #          `word-senses.csv`
        # Punctuation: [`comma`, `fullStop`] not part of original Sanskrit text
        #               but inserted in a separate layer
        # IsMantra: true if this word forms a part of a mantra as recorded in
        #           Bloomfield's Vedic Concordance
    ]

    def __init__(self, scheme=sanscript.DEVANAGARI):
        self.scheme = scheme

    # ----------------------------------------------------------------------- #

    def parse_conllu(self, dcs_conllu_content: str):
        """
        Parse a DCS CoNLL-U String

        Parameters
        ----------
        dcs_conllu_content : str
            Valid string of DCS CoNLL-U Data

        Returns
        -------
        list
            List of lines
        """
        conllu_lines = [
            line
            for line in conllu.parse(
                dcs_conllu_content,
                fields=self.FIELDS
            )
            if line
        ]

        # ------------------------------------------------------------------- #

        return self.transliterate_lines(conllu_lines)

    def parse_conllu_file(self, dcs_conllu_file: str or Path):
        """
        Parse a DCS CoNLL-U File

        Parameters
        ----------
        dcs_conllu_file : str or Path
            Path to the DCS CoNLL-U File

        Returns
        -------
        list
            List of lines
        """

        with open(dcs_conllu_file, encoding="utf-8") as f:
            content = f.read()

        return self.parse_conllu(content)

    # ----------------------------------------------------------------------- #

    def transliterate_lines(self, conllu_lines):
        """Transliterate CoNLL-U Data"""
        if self.scheme != self.INTERNAL_SCHEME:
            for textline in conllu_lines:
                textline.metadata = self.transliterate_metadata(
                    textline.metadata
                )
                for token in textline:
                    token = self.transliterate_token(token)
        return conllu_lines

    def transliterate_metadata(self, metadata):
        """Transliterate Metadata"""
        if self.scheme == self.INTERNAL_SCHEME:
            return metadata
        transliterate_keys = ["text"]
        for key in transliterate_keys:
            if key not in metadata:
                continue
            metadata[key] = transliterate(
                metadata[key], self.INTERNAL_SCHEME, self.scheme
            )
        return metadata

    def transliterate_token(self, token):
        """Transliterate Token"""
        if self.scheme == self.INTERNAL_SCHEME:
            return token

        transliterate_keys = ["form", "lemma", "misc.Unsandhied"]
        for key in transliterate_keys:
            if "." in key:
                _key, _subkey = key.split(".", 1)
            else:
                _key = key
                _subkey = None

            if _key not in token:
                continue

            if token[_key] is None:
                continue

            if _subkey is None:
                token[_key] = transliterate(
                    token[_key], self.INTERNAL_SCHEME, self.scheme
                )
            else:
                if token[_key][_subkey] is None:
                    continue
                token[_key][_subkey] = transliterate(
                    token[_key][_subkey], self.INTERNAL_SCHEME, self.scheme
                )
        return token

    # ----------------------------------------------------------------------- #

    def read_conllu_data(self, dcs_conllu_data: str):
        """
        Parse a DCS CoNLL-U File
        Prepare it for Data Input (Group Verses etc)

        Parameters
        ----------
        dcs_conllu_data : str
            DCS CoNLL-U Content
        """

        data = self.parse_conllu(dcs_conllu_data)
        chapter_lines = []

        for line in data:
            try:
                unit = {
                    "id": int(line.metadata["sent_id"]),
                    "verse_id": int(line.metadata["sent_counter"]),
                    "text": line.metadata["text"],
                    "tokens": [
                        {
                            "id": token.get("id") or "",
                            "form": token.get("form") or "",
                            "lemma": token.get("lemma") or "",
                            "upos": token.get("upos") or "",
                            "xpos": token.get("xpos") or "",
                            "feats": token.get("feats") or {},
                            "misc": token.get("misc") or {}
                        }
                        for token in line
                    ]
                }
                chapter_lines.append(unit)
            except Exception as e:
                print(line)
                raise e

        # Group verses
        verses = []
        last_verse_id = None
        for _line in chapter_lines:
            line_verse_id = _line.get("verse_id")
            if line_verse_id is None or line_verse_id != last_verse_id:
                last_verse_id = line_verse_id
                verses.append([])
            verses[-1].append(_line)

        return verses

    # ----------------------------------------------------------------------- #

###############################################################################
