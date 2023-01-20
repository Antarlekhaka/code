# Tables

* This folder contains sample data to illustrate format of various tables.
* File name should be `table_name.json` or `table_name.csv` (for `_Label ` tables)
* Please refer to `sample/` directory for examples.
* The files can be uploaded through Admin tab for bulk ontology update.

## Schema

* **JSON**: `List[Dict[str, str]]`: Mandatory keys as per schema
* **CSV**: Mandatory columns as per schema

* Task Table (`task.json`)
 - `id`
 - `name`
 - `title`
 - `short`
 - `help`

* Label Tables (`token_label.json`, `token_relation_label.json`, `sentence_label.json`, `sentence_relation_label.json`)
  - `label`
  - `description`

