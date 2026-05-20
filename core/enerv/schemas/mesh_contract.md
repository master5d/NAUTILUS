# ENERV Data Mesh Contract v1.0

## Principles (Adam Bellemare / Confluent)
1. **Facts are Immutable**: Once ingested, a node in Graphiti cannot be modified, only superseded by a new version.
2. **Timestamped**: Every entry must have `ingested_at` and `source_timestamp`.
3. **Reproducible**: The path from RAW to PRODUCT must be traceable.

## ACL (Anti-Corruption Layer) Schema
All incoming data from outside (Gmail, Web) must be re-modeled into these facets:
- `identity`: Who/What is the subject?
- `intent`: What is the goal/action?
- `context`: Where does it fit in ACE/ENERV?
- `signal_strength`: 0.0 - 1.0 (Importance)
