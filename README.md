# Antarlekhaka

A web-based distributed multi-task annotation framework following sequential annotation method.

## Installation Instructions

* Clone repository
* `pip install -r requirements.txt`
* Copy `settings.sample.py` to `settings.py` and make appropriate changes.
* Run application server `python server.py`

**Note**: Sample corpus and table data is included in `data/corpus/sample` and `data/tables/sample` respectively.

## Supported Tasks

* Task 1: Sentence Boundary
* Task 2: Canonical Word Order (Anvaya)
* Task 3: Token Classification (e.g. Named Entity Recognition)
* Task 4: Token Graph
* Task 5: Co-reference Resolution (special case of Token Graph)
* Task 6: Sentence Classification
* Task 7: Inter-sentence Connection (e.g. Discourse Graph)
* Task 8: Token Text Annotation (e.g. Lemmatization)
