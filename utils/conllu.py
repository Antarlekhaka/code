#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCS CoNLL-U Parsing Utility

@author: Hrishikesh Terdalkar
"""

from pathlib import Path
from typing import Tuple

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
        "id",  # 01
        "form",  # 02 word form or punctuation symbol
        # if it contains multiple words, the annotation
        # follows the proposals for multiword annotation
        # (URL: format.html#words-tokens-and-empty-nodes)
        "lemma",  # 03 lemma or stem, lexical id of lemma is in column 11
        "upos",  # 04 universal POS tags
        "xpos",  # 05 language specific POS tags, described in `pos.csv`
        "feats",  # 06
        "head",  # 07
        "deprel",  # 08
        "deps",  # 09
        "misc",  # 10
        "lemma_id",  # 11 numeric, matches first column of `dictionary.csv`
        "unsandhied",  # 12
        "sense_id",  # 13 numeric, matches first column of `word-senses.csv`
    ]
    METADATA_INFO = {
        "text_line": "text",
        "text_line_id": "line_id",
        "text_line_counter": "chapter_verse_id",
        "text_line_subcounter": "verse_line_id",
    }

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
                fields=self.FIELDS,
                metadata_parsers={"__fallback__": self._metadata_parser}
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

        transliterate_keys = ["form", "lemma", "unsandhied"]
        for key in transliterate_keys:
            if key not in token:
                continue
            token[key] = transliterate(
                token[key], self.INTERNAL_SCHEME, self.scheme
            )
        return token

    # ----------------------------------------------------------------------- #

    def _metadata_parser(self, k: str, v: str) -> Tuple[str, str]:
        """Metadata Parser for `conllu.parse()`"""
        parts = k.split(":", 1)

        key = parts[0].strip()
        value = parts[1].strip()

        key = self.METADATA_INFO.get(key, key)

        if key in ["line_id", "chapter_verse_id", "verse_line_id"]:
            value = parse_int(value)

        return key, value


###############################################################################
