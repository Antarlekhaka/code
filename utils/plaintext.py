#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plaintext Processing Utility

@author: Hrishikesh Terdalkar
"""

###############################################################################

import re
from typing import List

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# import stanza

###############################################################################


class Tokenizer:
    """Regular-expressions-based Tokenizer

    To split a string using a regular expression, which matches
    either the tokens or the separators between tokens.

    Parameters
    ----------
    pattern : str
        The pattern used to build tokenizer
    gaps : bool, optional
        If True, the pattern is used to find separators between tokens.
        otherwise, the pattern is used to find the tokens themselves.
        The default is True.
    discard_empty : bool, optional
        If True, any empty tokens are discarded.
        The default is True.
    flags : int, optional
        Regexp flags used to compile the tokenizer pattern.
        The default is: re.UNICODE | re.MULTILINE | re.DOTALL
    """

    def __init__(
        self,
        pattern: str,
        gaps: bool = True,
        discard_empty: bool = True,
        flags=re.UNICODE | re.MULTILINE | re.DOTALL
    ):
        pattern = getattr(pattern, "pattern", pattern)
        self._pattern = pattern
        self._gaps = gaps
        self._discard_empty = discard_empty
        self._flags = flags
        self._regexp = re.compile(pattern, flags)

    def tokenize(self, text: str) -> List[str]:
        """Tokenize the given text

        Parameters
        ----------
        text : str
            Text to be tokenized

        Returns
        -------
        List[str]
            List of tokens
        """
        if self._gaps:
            if self._discard_empty:
                return [token for token in self._regexp.split(text) if token]
            else:
                return self._regexp.split(text)
        else:
            return self._regexp.findall(text)


###############################################################################


class PlaintextProcessor:
    def __init__(
        self,
        input_scheme: str = sanscript.IAST,
        store_scheme: str = sanscript.DEVANAGARI,
    ):
        """Plaintext Files Processor

        Parameters
        ----------
        input_scheme : str, optional
            Input transliteration scheme
            The default is `sanscript.IAST`
        store_scheme : str, optional
            Transliteration scheme used to store the corpus in the database
            The default is `sanscript.DEVANAGARI`
        """
        self.input_scheme = input_scheme
        self.store_scheme = store_scheme

    # ----------------------------------------------------------------------- #
    # NOTE: Verse Data Format
    # [[{}, {}, {}, ...], [{}, {}, {}, ...], ...]
    # data: list of verses
    # verse: list of lines
    # line: dict (id, verse_id, text, tokens)
    # tokens: list of dict
    # token: dict 10 CoNLL-U mandatory fields
    # in particular,
    # "id", "form", "lemma", "upos", "xpos", "feats", "misc"

    def process(
        self,
        input_text: str,
        verse_separator_regex: str = r'\s*\n\s*\n\s*',
        line_separator_regex: str = r'\s*\n\s*',
        word_separator_regex: str = r'\s+'
    ):
        verse_tokenizer = Tokenizer(verse_separator_regex)
        line_tokenizer = Tokenizer(line_separator_regex)
        word_tokenizer = Tokenizer(word_separator_regex)

        store_text = self.transliterate(input_text)
        data = [
            [
                {
                    "id": None,
                    "verse_id": None,
                    "text": _line,
                    "tokens": [
                        {
                            "id": None,
                            "form": _word,
                            "lemma": "_",
                            "upos": "_",
                            "xpos": "_",
                            "feats": {},
                            "misc": {}
                        }
                        for _word in word_tokenizer.tokenize(_line)
                    ]
                }
                for _line in line_tokenizer.tokenize(_verse)
            ]
            for _verse in verse_tokenizer.tokenize(store_text)
        ]
        return data

    # def stanza_process(self, input_text: str, language_code: str):
    #     store_text = self.transliterate(input_text)
    #     nlp = stanza.Pipeline(language_code)
    #     doc = nlp(store_text)

    def transliterate(self, s: str) -> str:
        return transliterate(s, self.input_scheme, self.store_scheme)

    # ----------------------------------------------------------------------- #

###############################################################################
