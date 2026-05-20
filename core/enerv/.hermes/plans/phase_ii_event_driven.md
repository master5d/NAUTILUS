# Implementation Plan: Phase II - Event-Driven Ingest

## Goal
Transform ENERV from a batch-processing "data lake" into a real-time "Data Mesh" using Event Streams and Anti-Corruption Layer (ACL).

## Architecture Changes
1. **Source Layer (Fastmail/Gmail)**: Switch from polling to IMAP IDLE / Webhooks.
2. **Transport Layer (n8n)**: 
   - Workflow trigger: Webhook or IMAP Trigger.
   - Initial processing: De-duplication and PII Redaction.
3. **ACL Layer (Hermes/ENERV)**:
   - Schema enforcement using `.schemas/mesh_contract.md`.
   - Transformation of raw email to "Data Product" (Facet re-modeling).
4. **Sink Layer (Graphiti/Obsidian)**:
   - Immutable write to `/products/`.
   - Real-time graph updates via FalkorDB.

## Tasks
- [ ] Configure n8n Webhook for real-time ingest.
- [ ] Implement `ACL Transformer` script (Python).
- [ ] Update `enerv-mesh-validator` skill with automated schema checks.
- [ ] Establish "Dead Letter Queue" for failed contracts.

## Verification
- Latency < 10s from email arrival to Obsidian record creation.
- 100% compliance with F.A.C.T.S principles.
