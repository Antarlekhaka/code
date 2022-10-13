# Tables

This folder contains data to initialize various tables on the first run.

File name should be `table_name.json`

**TODO**: Support for CSV files.

**NOTE**: Check `sample/` folder for examples.

## Schema


* Task Table (`task.json`)
 - `id`
 - `name`
 - `title`
 - `short`
 - `help`

* Label Tables (`entity_label.json`, `relation_label.json`, `sentence_label.json`, `discourse_label.json`)
  - `label`
  - `description`
