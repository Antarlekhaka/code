# Miscellaneous

## SQL Queries

* `queries.sql` - contains SQL query for tracking progress of annotators
* `apply_database_changes_task_category.sql` - contains SQL transformations to apply to old databases (before `feature/task-category`) to make them compatible with addition of `task_id` to all annotation tables.


## Python Scripts

### Bulk Add Data

* `bulk_add_chapter.py` - add chapters in bulk
* `bulk_create_user.py` - create user accounts in bulk

### Fix Analysis

* `fix_multitoken_analysis.py` - script to fix missing analysis of multitokens
* `fix_missing_analysis.py` - script to fix missing analysis of custom tokens [INCOMPLETE]

## Corpus Specific

* `corpus_statistics.py` - get DCS corpus statistics
  - requires DCS corpus to be present in `data/corpus/dcs/`
  - reads `data/corpus/dcs/*.conllu` and writes multiple files to `data/corpus/dcs/stats/`
  - can be customized to suit specific corpus needs
  - does not change database, merely queries it
