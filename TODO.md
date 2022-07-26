## BUGS

- [ ] After marking sentence boundary, transition to anvaya task doesnt take proper sentence as anvaya, need to call `setup_anvaya()` again. Probably async issue.
- [ ] When new boundaries are marked, it may affect next sentence as well, need to do something about that. (e.g. If token 12 was boundary, and token 24 was another, and token 12 gets deleted, now, if token 24 had anvaya, that needs to be re-done)

## TODO

- [ ] Front-end
  - [x] Sentence Boundary Interface
  - [x] Anvaya Interface
  - [x] Named Entity Interface
  - [ ] Action Graph Interface
  - [ ] Coreference Resolution Interface
- [ ] Back-end
  - [ ] Recording Sentence Boundary
    - [x] Core functionality
    - [x] Deleting necessary boundaries if required
    - [ ] Extensive testing
  - [ ] Recording Anvaya
    - [x] Core functionality
    - [ ] Extensive testing
  - [ ] Named Entity Recognition
    - [ ] Core functionality
    - [ ] Extensive testing
  - [ ] Action Graph
    - [ ] Core functionality
    - [ ] Extensive testing
  - [ ] Co-reference Resolution
    - [ ] Core functionality
    - [ ] Extensive testing

