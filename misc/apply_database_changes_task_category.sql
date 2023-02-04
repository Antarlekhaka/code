/* ************************ Data Transfer Commands ************************ */
/* CAUTION:
  DO NOT USE THIS SCRIPT IF YOU HAVE STARTED USING THE SYSTEM AFTER BETA
  RELEASE v0.1.0.
*/
/* LOGIC:
* Rename relevant tables to `old_*` and drop relevant indexes
* Restart server to create as per new schema
* Copy data from `old_*` tables to respective tables
* Remove `old_*` tables
*/

/* ACTION: STOP SERVER */

/* Bring the tasks are in a default order */
UPDATE `task` SET `id` = `id` + 10, `order` = `order` + 10;
UPDATE `task` SET `id` = 1, `order` = 1 WHERE `category` = 'sentence_boundary';
UPDATE `task` SET `id` = 2, `order` = 2 WHERE `category` = 'word_order';
UPDATE `task` SET `id` = 3, `order` = 3 WHERE `category` = 'token_text_annotation';
UPDATE `task` SET `id` = 4, `order` = 4 WHERE `category` = 'token_classification';
UPDATE `task` SET `id` = 5, `order` = 5 WHERE `category` = 'token_graph';
UPDATE `task` SET `id` = 6, `order` = 6 WHERE `category` = 'token_connection';
UPDATE `task` SET `id` = 7, `order` = 7 WHERE `category` = 'sentence_classification';
UPDATE `task` SET `id` = 8, `order` = 8 WHERE `category` = 'sentence_graph';

/* Move old tables */
ALTER TABLE `task` RENAME TO `old_task`;
ALTER TABLE `submit_log` RENAME TO `old_submit_log`;
ALTER TABLE `boundary` RENAME TO `old_boundary`;
ALTER TABLE `word_order` RENAME TO `old_word_order`;
ALTER TABLE `token_text_annotation` RENAME TO `old_token_text_annotation`;
ALTER TABLE `token_classification` RENAME TO `old_token_classification`;
ALTER TABLE `token_graph` RENAME TO `old_token_graph`;
ALTER TABLE `token_connection` RENAME TO `old_token_connection`;
ALTER TABLE `sentence_classification` RENAME TO `old_sentence_classification`;
ALTER TABLE `sentence_graph` RENAME TO `old_sentence_graph`;
ALTER TABLE `token_label` RENAME TO `old_token_label`;
ALTER TABLE `token_relation_label` RENAME TO `old_token_relation_label`;
ALTER TABLE `sentence_label` RENAME TO `old_sentence_label`;
ALTER TABLE `sentence_relation_label` RENAME TO `old_sentence_relation_label`;

/* Drop old indexes */
DROP INDEX ix_submit_log_verse_id;
DROP INDEX ix_boundary_verse_id;
DROP INDEX boundary_token_id_annotator_id;
DROP INDEX word_order_boundary_id_annotator_id_token_id;
DROP INDEX token_text_annotation_token_id_annotator_id;
DROP INDEX token_classification_token_id_annotator_id;
DROP INDEX token_graph_annotator_id_src_id_dst_id;
DROP INDEX token_connetion_annotator_id_src_id_dst_id;
DROP INDEX sentence_classification_annotator_id_boundary_id;
DROP INDEX sentence_graph_annotator_id_src_boundary_id_dst_boundary_id_src_token_id_dst_token_id_relation_type;

/* BEFORE PROCEEDING FURTHER, */
/* ACTION: START SERVER */
/* ACTION: VISIT ANY PATH (THIS WILL RECREATE MISSING TABLES AS PER NEW SCHEMA) */

/* ******************************* Copy Data ******************************* */

/* Copy Tasks */
DELETE FROM `task` WHERE 1;
INSERT INTO `task` SELECT * FROM `old_task`;
INSERT INTO `submit_log` SELECT * FROM `old_submit_log`;

/* Copy Ontology */
INSERT INTO `token_label` (`id`, `task_id`, `label`, `description`, `is_deleted`)
SELECT `id`, 4, `label`, `description`, `is_deleted` FROM `old_token_label`;

INSERT INTO `token_relation_label` (`id`, `task_id`, `label`, `description`, `is_deleted`)
SELECT `id`, 5, `label`, `description`, `is_deleted` FROM `old_token_relation_label`;

INSERT INTO `sentence_label` (`id`, `task_id`, `label`, `description`, `is_deleted`)
SELECT `id`, 7, `label`, `description`, `is_deleted` FROM `old_sentence_label`;

INSERT INTO `sentence_relation_label` (`id`, `task_id`, `label`, `description`, `is_deleted`)
SELECT `id`, 8, `label`, `description`, `is_deleted` FROM `old_sentence_relation_label`;

/* Copy Annotations */
INSERT INTO `boundary` (`id`, `task_id`, `verse_id`, `token_id`, `annotator_id`, `updated_at`)
SELECT `id`, 1, `verse_id`, `token_id`, `annotator_id`, `updated_at` FROM `old_boundary`;

INSERT INTO `word_order` (`id`, `task_id`, `boundary_id`, `token_id`, `order`, `annotator_id`, `updated_at`)
SELECT `id`, 2, `boundary_id`, `token_id`, `order`, `annotator_id`, `updated_at` FROM `old_word_order`;

INSERT INTO `token_text_annotation` (`id`, `task_id`, `boundary_id`, `token_id`, `text`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 3, `boundary_id`, `token_id`, `text`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_token_text_annotation`;

INSERT INTO `token_classification` (`id`, `task_id`, `boundary_id`, `token_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 4, `boundary_id`, `token_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_token_classification`;

INSERT INTO `token_graph` (`id`, `task_id`, `boundary_id`, `src_id`, `label_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 5, `boundary_id`, `src_id`, `label_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_token_graph`;

INSERT INTO `token_connection` (`id`, `task_id`, `boundary_id`, `src_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 6, `boundary_id`, `src_id`, `dst_id`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_token_connection`;

INSERT INTO `sentence_classification` (`id`, `task_id`, `boundary_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 7, `boundary_id`, `label_id`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_sentence_classification`;

INSERT INTO `sentence_graph` (`id`, `task_id`, `src_boundary_id`, `dst_boundary_id`, `src_token_id`, `dst_token_id`, `label_id`, `relation_type`, `annotator_id`, `is_deleted`, `updated_at`)
SELECT `id`, 8, `src_boundary_id`, `dst_boundary_id`, `src_token_id`, `dst_token_id`, `label_id`, `relation_type`, `annotator_id`, `is_deleted`, `updated_at` FROM `old_sentence_graph`;


/* **************************** Remove Old Data **************************** */

DROP TABLE `old_task`;
DROP TABLE `old_submit_log`;
DROP TABLE `old_token_label`;
DROP TABLE `old_token_relation_label`;
DROP TABLE `old_sentence_label`;
DROP TABLE `old_sentence_relation_label`;
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
