#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix analysis associated with multitokens

Corpus: Digital Corpus of Sanskrit (DCS)

Multitokens are tokens from DCS with ID of the form 1-4, which indicates that
the token is broken down into multiple parts and subtokens have ID 1 to 4.
Observed phenomenon is that multitokens themselves don't have any analysis
associated with them.
Therefore, heuristic we use to fix this is apply the analysis of last subtoken
to the parent multitoken.


Created on Wed May 10 17:59:29 2023

@author: Hrishikesh Terdalkar
"""

from sqlalchemy.orm.attributes import flag_modified

from explore_database import db, Token

###############################################################################

update_tokens = []
current_multitoken = None
next_n = 0

for token in Token.query.all():
    if '-' in token.inner_id:
        current_multitoken = token
        start, end = map(int, token.inner_id.split('-'))
        next_n = end - start + 1

    if current_multitoken is not None:
        if next_n:
            next_n -= 1
            continue
        else:
            # target = (
            #     current_token,
            #     current_token.analysis['form'],
            #     token,
            #     token.analysis['form']
            # )
            update_tokens.append(current_multitoken.id)
            current_multitoken.analysis['upos'] = token.analysis['upos']
            current_multitoken.analysis['feats'] = token.analysis['feats']
            flag_modified(current_multitoken, "analysis")
            db.session.add(current_multitoken)
            current_multitoken = None


print(f"Updating {len(update_tokens)} tokens ...")
db.session.commit()
print("Done!")

###############################################################################
