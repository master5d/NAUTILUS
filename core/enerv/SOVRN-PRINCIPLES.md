# ENERV Sovereign Principles (v3.3 — Mesh Evolution)

## 1. Zero Telemetry & Local First
All core data processing (ACL Transformation, Indexing, Vector Extraction) happens behind the Sovereign Door. External LLMs are used via LiteLLM as "stateless compute units" only; the "Brain" and "State" reside in WSL/Local Storage.

## 2. Memory as a Data Mesh (Data-as-a-Product)
We reject the "Data Lake" model of dumping raw files. 
- **Enforcement**: No data enters the ENERV Graph or ACE framework without passing the **Anti-Corruption Layer (ACL)**.
- **F.A.C.T.S Framework**: 
  - **F**acts are Immutable.
  - **A**udit Trails on every record.
  - **C**ontract-First (Schemas define valid data).
  - **T**imestamped at origin and ingest.
  - **S**overeignly Controlled.

## 3. Orchestrator-in-Chief (Hermes Role)
Hermes is the gatekeeper of memory. Sub-agents (Coders, Researchers) interact with data only through Hermes-provided context windows, preventing tool/context sprawl and protecting the user's ACE framework.

## 4. Federated Ownership
Data "Ownership" is assigned to specific ENERV domains (e.g., `tech/enerv`, `knowledge/ace`). Cross-domain dependencies are managed via Federated Links in Graphiti (Phase 1).
