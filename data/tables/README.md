# Tables

* This folder contains data to initialize various tables on the first run.
* File name should be `table_name.json` or `table_name.csv` (for `_Label ` tables)
  - If both are present, `.json` takes priority over `.csv`
  - **TODO**: Add CSV support for task table
* Please refer to `sample/` directory for examples.



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

