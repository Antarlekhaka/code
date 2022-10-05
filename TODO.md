## TODO

- [ ] DiscourseGraph show graph

- [ ] Admin
  - [ ] Download Data
  - [ ] Task Reorder/Enable/Disable
  - [ ] View as another user

- [ ] "Submit and go to next verse" ?

- [ ] Unify/Modularize task backend handling items? (Task-3 onwards, since most of it is repetitive code).
- [ ] Remove `task_id` hardcoding

- [ ] Improvements to "Add Token" Interface
  - [x] Front-end with multiple fields for Analysis and Features
  - [ ] Search Functionality for "Add Token"
  - [ ] Edit Token using same interface?

- [ ] Keep showing the TokenGraph as triplets are added
  - [x] Core functionality - after press of a button
  - [ ] Change graph to show permanently instead of on click

---

- [x] Add triplets for token graph
- [x] Show sentence with Token Graph
- [x] Do task setup on the event of tab change (so we can avoid calling it from every submit and it'll be more consistent)
- [x] Track progress and provide a progressbar in front-end
  - [x] Front-end (formatter function, on-hover info)
  - [x] Back-end (update after every task-submit)
- [x] Skip vs Submit
  [x] Remove Skip button?
  [x] Allow empty submits
- [x] Draggable Left-Right Column
  - [x] ~At least adjust width (50-50 or so)~ (no longer needed)


## Bugs

- [ ] If there are deleted items, it triggers a "Successfully updated" message even if there are no changes. Refer to `server_sqla.py` for further details.

- [x] After marking sentence boundary, transition to anvaya task doesnt take proper sentence as anvaya, need to call `setup_anvaya()` again. Probably async issue.
- [x] When new boundaries are marked, it may affect next sentence as well, need to do something about that. (e.g. If token 12 was boundary, and token 24 was another, and token 12 gets deleted, now, if token 24 had anvaya, that needs to be re-done)

## Core

- [x] Front-end
  - [x] Sentence Boundary Interface
  - [x] Anvaya Interface
    - [x] Reordering Front-end (sortable)
  - [x] Named Entity Interface
  - [x] Token Graph Interface
    - [x] Triplet based addition
    - [x] Show Live Graph (on button click)
  - [x] Coreference Resolution Interface
    - [x] Button click (for token selection) based interface
  - [x] Sentence Classification Interface
  - [x] Intersentence Connection (Discourse Graph)
- [x] Back-end
  - [x] Sentence Boundary
    - [x] Deleting necessary boundaries if required
    - [x] Delete related objects
  - [x] Anvaya
  - [x] Named Entity Recognition
  - [x] Token Graph
  - [x] Co-reference Resolution
  - [x] Sentence Classification
  - [x] Intersentence Connection

## Future

- [ ] Allow selecting if DCS etc in case that conllu allowed
- [ ] Run SSCS for splitting (for general Sanskrit corpus when not in CoNLLU) (Think!)
- [ ] Addition of dynamic tasks from Admin panel
- [ ] Edit in table??
- [ ] Allow multiple selection in classification tasks -- handle it on JS side, generating multiple entries from a single selector -- Issue: when it is actually
single select, multi-select adds one extra click for changing.
