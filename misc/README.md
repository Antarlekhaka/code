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
