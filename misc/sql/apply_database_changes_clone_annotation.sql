/* ************************ Data Transfer Commands ************************ */
/* CAUTION:
  DO NOT USE THIS SCRIPT IF YOU HAVE STARTED USING THE SYSTEM AFTER BETA
  RELEASE v0.2.0.
*/
/* CHANGE:
* Add two new columns to all annotation tables
* - `is_clone`: boolean, default false, not null
* - `cloned_from_id`: integer, foreign key referencing self-table
*/
/* LOGIC:
* ADD CONSTRAINT variant of ALTER TABLE command is not supported by SQLite.
* (Reference: https://stackoverflow.com/questions/1884818/how-do-i-add-a-foreign-key-to-an-existing-sqlite-table)
* Therefore,
* Rename relevant tables to `old_*` and drop relevant indexes
* Restart server to create as per new schema
* Copy data from `old_*` tables to respective tables
* Remove `old_*` tables
*/


/* ACTION: STOP SERVER */

/* Move old tables */
ALTER TABLE `boundary` RENAME TO `old_boundary`;
ALTER TABLE `word_order` RENAME TO `old_word_order`;
ALTER TABLE `token_text_annotation` RENAME TO `old_token_text_annotation`;
ALTER TABLE `token_classification` RENAME TO `old_token_classification`;
ALTER TABLE `token_graph` RENAME TO `old_token_graph`;
ALTER TABLE `token_connection` RENAME TO `old_token_connection`;
ALTER TABLE `sentence_classification` RENAME TO `old_sentence_classification`;
ALTER TABLE `sentence_graph` RENAME TO `old_sentence_graph`;

/* Drop old indexes */

DROP INDEX ix_boundary_verse_id;
DROP INDEX ix_boundary_task_id;
DROP INDEX boundary_token_id_annotator_id;

DROP INDEX ix_word_order_task_id;
DROP INDEX word_order_boundary_id_annotator_id_token_id;

DROP INDEX ix_token_text_annotation_task_id;
DROP INDEX token_text_annotation_task_id_annotator_id_token_id;

DROP INDEX ix_token_classification_task_id;
DROP INDEX token_classification_task_id_annotator_id_token_id;

DROP INDEX ix_token_graph_task_id;
DROP INDEX token_graph_task_id_annotator_id_src_id_dst_id;

DROP INDEX ix_token_connection_task_id;
DROP INDEX token_connection_task_id_annotator_id_src_id_dst_id;

DROP INDEX ix_sentence_classification_task_id;
DROP INDEX sentence_classification_task_id_annotator_id_boundary_id;

DROP INDEX ix_sentence_graph_task_id;
DROP INDEX sentence_graph_task_id_annotator_id_src_boundary_id_dst_boundary_id_src_token_id_dst_token_id_relation_type;

/* BEFORE PROCEEDING FURTHER, */
/* ACTION: START SERVER */
 /* ACTION: REQUEST ANY ROUTE (THIS WILL RECREATE MISSING TABLES AS PER NEW SCHEMA) */

/* ******************************* Copy Data ******************************* */
/* Copy Annotations */

INSERT INTO `boundary` (`id`, `task_id`, `verse_id`, `token_id`, `annotator_id`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `verse_id`, `token_id`, `annotator_id`, `updated_at`, FALSE, NULL FROM `old_boundary`;

INSERT INTO `word_order` (`id`, `task_id`, `boundary_id`, `token_id`, `order`, `annotator_id`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `token_id`, `order`, `annotator_id`, `updated_at`, FALSE, NULL FROM `old_word_order`;

INSERT INTO `token_text_annotation` (`id`, `task_id`, `boundary_id`, `token_id`, `text`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `token_id`, `text`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_token_text_annotation`;

INSERT INTO `token_classification` (`id`, `task_id`, `boundary_id`, `token_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `token_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_token_classification`;

INSERT INTO `token_graph` (`id`, `task_id`, `boundary_id`, `src_id`, `label_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `src_id`, `label_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_token_graph`;

INSERT INTO `token_connection` (`id`, `task_id`, `boundary_id`, `src_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `src_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_token_connection`;

INSERT INTO `sentence_classification` (`id`, `task_id`, `boundary_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `boundary_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_sentence_classification`;

INSERT INTO `sentence_graph` (`id`, `task_id`, `src_boundary_id`, `dst_boundary_id`, `src_token_id`, `dst_token_id`, `label_id`, `relation_type`, `annotator_id`, `is_deleted`, `updated_at`, `is_clone`, `cloned_from_id`)
SELECT `id`, `task_id`, `src_boundary_id`, `dst_boundary_id`, `src_token_id`, `dst_token_id`, `label_id`, `relation_type`, `annotator_id`, `is_deleted`, `updated_at`, FALSE, NULL FROM `old_sentence_graph`;


/* **************************** Remove Old Data **************************** */

DROP TABLE `old_boundary`;
DROP TABLE `old_word_order`;
DROP TABLE `old_token_text_annotation`;
DROP TABLE `old_token_classification`;
DROP TABLE `old_token_graph`;
DROP TABLE `old_token_connection`;
DROP TABLE `old_sentence_classification`;
DROP TABLE `old_sentence_graph`;

/* SQLite3 Specific - clear deleted data from disk */
VACUUM;
