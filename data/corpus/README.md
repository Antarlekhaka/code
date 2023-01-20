# Corpus

The `sample/` folder contains sample data to illustrate data format.

## CoNLL-U Data

* Required metadata fields: `text`, `sent_id`, `sent_counter` (`sent_counter` denotes verse ID)

## Plaintext Data

* Regular expression based splits are performed (in order)
  - Verse separator regex: `\s*\n\s*\n\s*`
  - Line separator regex: `\s*\n\s*`
  - Word separator regex: `\s+`
