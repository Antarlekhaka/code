## Features

- [x] (Admin) Clone Annotations
  - [x] Required schema changes (boolean `is_clone` and integer `cloned_from_id` to keep track of source)
    - [x] Change models in `model_sqla.py`
    - [x] Add `.sql` in `misc/` that contains SQL migration commands
  - [x] Database function to clone annotations from one annotator to another
  - [x] Admin GUI to perform transfer

- [ ] (Admin) Show Annoation Progress
  - [x] Database utility function to fetch annotation progress (`utils.database.get_annotation_progress`)
    - [ ] Utilize `is_cloned` column to ensure cloned annotation stats are not credited to the user
  - [x] (tempoarary) Basic `jsonify()` frontend
  - [ ] Admin GUI to neatly display annotation progress

- [ ] Accept plaintext input
  - [x] Simple plaintext processor (regex split)
  - [ ] Stanza or some similar processors
  - [ ] Input/Output Transliteration option at the time of chapter file upload

- [ ] Use `localStorage` for QoL Improvement Changes
  - [ ] (corpus) split.js percentages
  - [ ] (corpus) custom style for unconfirmed annotations from each task
    - [x] (word-order) store unsubmitted word-order annotations (saved entities: `state`, `unsubmitted-order`, `heuristic-order`)
    - [x] (word-order) add badges to describe fixed annotation areas (sentence tokens, unused area, custom tokens)
    - [x] (word-order) display `state` badge to show the phase of annotation of each boundary element

  - [x] (admin) remember last open tab
    - [x] data management accordion
    - [x] ontology tabs

- [ ] Export Data
  - [ ] Every task in 2 formats
    - [x] suitable for annotators
    - [x] annotator visualization
    - [ ] (admin) suitable for programmers
    - [ ] decide a standard format

- [ ] (Admin) Download (Export) Data

- [x] (Admin) Task Reorder/Enable/Disable

- [ ] (Admin) View as another user

- [ ] Improvements to "Add Token" Interface
  - [x] Front-end with multiple fields for Analysis and Features
  - [ ] Search Functionality for "Add Token"
  - [ ] Edit Token using same interface?

- [ ] Keep showing the TokenGraph as triplets are added
  - [x] Core functionality - after press of a button
  - [ ] Change graph to show permanently instead of on click

- [ ] Unify/Modularize task backend handling items? (Task-3 onwards, since most of it is repetitive code).

- [ ] Remove `task_id` hardcoding
  - [x] Task table
  - [x] Remove `task_id` hard-coding in `server_sqla.py` api action handling
  - [x] Next task etc using Task.order
  - [x] Task related elements etc in JS
  - [ ] `export.py` hard-coding for Sentence Boundary and Token Order task

---

## Minor

- [ ] Custom key-events
  - [ ] Next/Previous Verse
  - [ ] Next/Previous Page
  - [ ] Submit

- [ ] "Submit and go to next verse" ?

---

## Implemented

- [x] Update Token Order task pipeline
  - [x] Present it as a two-step task
  - [x] Step 1: Decide which tokens to keep or get rid of
  - [x] Step 2: Decide token order (current full task)
- [x] Allow display of additional context when required
- [x] Task Category System (allow multiple tasks from same category)
  - [x] Global `TASK_CATEGORY` Constants
  - [x] Update models
    - [x] Task model to have `category` (`Enum()` of all valid task categories)
    - [x] All task models to have `task_id`
  - [x] Render templates, perform JS actions based on `Task.category`
  - [x] Admin interface to add/edit tasks, `category` to be chosen
    - [x] Customizable Help Messages
- [x] Log all Submits instead of just latest per task per annotator?
- [x] SentenceGraph show graph
- [x] Add triplets for token graph
- [x] Show sentence with Token Graph
- [x] Do task setup on the event of tab change (so we can avoid calling it from every submit and it'll be more consistent)
- [x] Track progress and provide a progressbar in front-end
  - [x] Front-end (formatter function, on-hover info)
  - [x] Back-end (update after every task-submit)
- [x] Skip vs Submit
  - [x] Remove Skip button?
  - [x] Allow empty submits
- [x] Draggable Left-Right Column
  - [x] ~At least adjust width (50-50 or so)~ (no longer needed)


## Bugs

- [ ] Multiple chapters selection in `export/` interface doesn't work, either force a single chapter, or figure out why the error is occurring
- [ ] If there are deleted items, it triggers a "Successfully updated" message even if there are no changes. Refer to `server_sqla.py` for further details.

- [x] TokenConnection/SentenceGraph connections/relations show incomplete rows when one of the tokens is out of context.
- [x] Export - boundary not shown in some cases
  - (details: bug was when boundary token does not have text (or equals `_`))
- [x] If sentence boundary is marked for a verse in the next chapter, all the nodes in between get counted as sentences
- [x] Task 4 not recording
- [x] Task 4 display only displays single relation out of existing ones
- [x] After marking sentence boundary, transition to word-order task doesn't take proper sentence as word-order, need to call `setup_word_order()` again. Probably async issue.
- [x] When new boundaries are marked, it may affect next sentence as well, need to do something about that. (e.g. If token 12 was boundary, and token 24 was another, and token 12 gets deleted, now, if token 24 had `word_order`, that needs to be re-done)

## Core

- [x] Front-end
  - [x] Sentence Boundary Interface
  - [x] Canonical Token Order Interface
    - [x] Reordering Front-end (sortable)
  - [x] Token Text Annotation Interface
  - [x] Token Classification Interface (e.g. Named Entity)
  - [x] Token Graph Interface
    - [x] Triplet based addition
    - [x] Show Live Graph (on button click)
  - [x] Co-reference Resolution Interface
    - [x] Button click (for token selection) based interface
  - [x] Sentence Classification Interface
  - [x] Sentence Graph
- [x] Back-end
  - [x] Sentence Boundary
    - [x] Deleting necessary boundaries if required
    - [x] Delete related objects
  - [x] Canonical Token Order
  - [x] Token Text Annotation
  - [x] Token Classification
  - [x] Token Graph
  - [x] Token Connection
  - [x] Sentence Classification
  - [x] Sentence Graph

## Future

- [ ] Connect to Sangrahaka
  - [ ] Import entities (do it manually in database)
- [ ] Allow selecting if DCS etc in case that conllu allowed
- [ ] Run SSCS for splitting (for general Sanskrit corpus when not in CoNLLU) (Think!)
- [ ] Edit in table??
- [ ] Allow multiple selection in classification tasks -- handle it on JS side, generating multiple entries from a single selector -- Issue: when it is actually
single select, multi-select adds one extra click for changing.
- [ ] User-wise task allocation?

- [ ] Conflict Resolution Strategy
  -  [ ] Task-specific
