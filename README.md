# Antarlekhaka

A web-based distributed multi-task annotation framework following sequential annotation method.

This work has been accepted in **3rd Workshop on NLP Open Source Software at the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP 2023)**.

## Installation Instructions

* Clone repository
* `pip install -r requirements.txt`
* Copy `settings.sample.py` to `settings.py` and make appropriate changes.
* Run application server `python server.py`

**Note**: Sample corpus and table data is included in `data/corpus/sample` and `data/tables/sample` respectively.

## Supported Tasks

* Task 1: Sentence Boundary
* Task 2: Canonical Token Order (a.k.a. Anvaya)
* Task 3: Token Classification (e.g. Named Entity Recognition)
* Task 4: Token Graph (e.g. Dependency Graph, Action Graph)
* Task 5: Token Connection (e.g. Co-reference Resolution)
* Task 6: Sentence Classification
* Task 7: Sentence Graph (e.g. Discourse Graph)
* Task 8: Token Text Annotation (e.g. Lemmatization)

## Cite

* Download Paper: [arXiv](https://arxiv.org/abs/2310.07826)

```
@inproceedings{terdalkar2023antarlekhaka,
  title         = {{Antarlekhaka}: A Comprehensive Tool for Multi-task Natural Language Annotation},
  author        = {Terdalkar, Hrishikesh and Bhattacharya, Arnab},
  year          = {2023},
  eprint        = {2310.07826},
  url           = {https://arxiv.org/abs/2310.07826},
  publisher     = {Association for Computational Linguistics},
  archiveprefix = {arXiv},
  keywords      = {Annotation Tool, Sequential Annotation, Natural Language Processing},
  booktitle     = {Proceedings of the 3rd Workshop on NLP Open Source Software at the 2023 Conference on Empirical Methods in Natural Language Processing},
  primaryclass  = {cs.CL},
  numpages      = {8},
  location      = {Singapore},
  series        = {NLP-OSS @ EMNLP}
}
```
