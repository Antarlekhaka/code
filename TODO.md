## TODO

[ ] Improvments to "Add Token" Interface
  - [ ] Front-end with multiple fields for Analysis and Features
  - [ ] Search Functionality for "Add Token"
  - [ ] Edit Token using same interface?

[ ] Track progress and provide a progressbar in front-end
  - [x] Front-end
  - [ ] Back-end

[ ] View as another user for Admin

### Features

[ ] Draggable Left-Right Column?
  - [x] At least adjust width (50-50 or so)
[ ] Skip vs Submit
  [x] Remove Skip button?
  [x] Allow empty submits
[ ] Keep showing the graph as triplets are added
  - [x] Core functionality - after press of a button
  - [ ] Change graph to show permanently instead of on click

[x] Add triplets for token graph
[x] Show sentence with Token Graph
[x] Do task setup on the event of tab change (so we can avoid calling it from every submit and it'll be more consistent)

## BUGS

- [x] After marking sentence boundary, transition to anvaya task doesnt take proper sentence as anvaya, need to call `setup_anvaya()` again. Probably async issue.
- [x] When new boundaries are marked, it may affect next sentence as well, need to do something about that. (e.g. If token 12 was boundary, and token 24 was another, and token 12 gets deleted, now, if token 24 had anvaya, that needs to be re-done)

### Core

- [ ] Front-end
  - [x] Sentence Boundary Interface
  - [x] Anvaya Interface
  - [x] Named Entity Interface
  - [x] Token Graph Interface
  - [x] Coreference Resolution Interface
  - [x] Sentence Classification Interface
  - [x] Intersentence Connection
- [ ] Back-end
  - [ ] Sentence Boundary
    - [x] Core functionality
    - [x] Deleting necessary boundaries if required
    - [ ] Extensive testing
  - [ ] Anvaya
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Named Entity Recognition
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Token Graph
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Co-reference Resolution
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Sentence Classification
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Intersentence Connection
    - [x] Core functionality
    - [ ] Extensive testing

### Future

[ ] Allow selecting if DCS etc in case that conllu allowed
[ ] Run SSCS for splitting (for general Sanskrit corpus when not in CoNLLU) (Think!)
[ ] Addition of dynamic tasks from Admin panel
[ ] Edit in table??
[ ] Allow multiple selection in classification tasks -- handle it on JS side, generating multiple entries from a single selector -- Issue: when it is actually
single select, multi-select adds one extra click for changing.
