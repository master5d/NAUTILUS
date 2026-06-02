# DesOps Standard (NAUTILUS)

## 1. The Design Harness (3-Layer Model)
The NAUTILUS Design Harness is an implementation of **Google-grade Agentic Design Patterns** (Antonio Gulli), optimizing the flow from high-level intent to production-ready artifacts.

### Layer 1: Skills (The Expertise)
We "borrow taste" from seasoned designers by installing expert logic directly into our AI agents' context.
- **Rule Zero: Fact Verification First:** If a task mentions a specific product, brand, or technology, the agent MUST perform a web search to verify existence, versions, and official specifications before starting.
- **Automated System Generation:** Use specialized skills (e.g., `ui-ux-pro-max`) to generate complete design systems in seconds.
- **Core Asset Protocol:** To eliminate brand hallucination, agents MUST gather 6 types of assets (logo, product photos, UI screenshots, palette, fonts, guidelines) via official sources before designing.
- **Design Protocols:** We load specific methodologies (e.g., `huashu-design`) as agentic skills.
- **Reflection & Self-Correction (Ch. 4):** Agents MUST perform a 5-angle self-audit based on 20+ design principles. The agent acts as its own harshest critic before human review.
- **Anti-Generic Layer & Anti-Slop:** Use specialized skills to eliminate "AI-slop."
- **Anti-Pattern Guardrails & Safety (Ch. 18):** Automated linting MUST include accessibility (WCAG) and neuro-inclusive checks to prevent "design hallucinations."
  - ❌ **No Pure Blacks:** Avoid `#000000`. Use deep system grays/blues defined in tokens.
  - ❌ **No Gray-on-Color:** Strictly enforce WCAG contrast.
  - ❌ **No Nested Cards:** Simplify hierarchy.
- **Expert Commands:** `/audit`, `/polish`, `/delight`.

### Layer 2: Agent Canvas (The Surface)
Design occurs on agent-native surfaces using the **Model Context Protocol (MCP, Ch. 10)** to ensure seamless interoperability between tools.
- **Paper:** Real HTML/CSS canvas for direct component logic.
- **Pencil / OpenPencil:** JSON-based formats for vector precision.
- **Parallelization (Ch. 3):** We leverage concurrent agent teams (via OpenPencil) to design Hero sections, tokens, and layouts in parallel.

### Layer 3: The Eye (Visual DNA)
We train our "eye" and the agent's "taste" by absorbing visual DNA from curated sources.
- **Industry Intelligence:** Leverage databases of 161+ color palettes and 57+ font pairings.
- **Style Dropping:** Extract visual DNA from Mobbin, Awwwards, and Cosmos.
- **Brand Injection:** Use pre-validated `DESIGN.md` archetypes (e.g., `awesome-claude-design`).
- **Asset Orchestration (Illustrations):** Prioritize modular, SVG-based libraries.

## 2. Tools & Workflow
- **Stitch / Open-Codesign:** For high-level generative UI and multi-model (BYOK) variations.
- **UI UX Pro Max:** For automated Design System generation.
- **Pencil / OpenPencil:** For vector precision and Git-integrated concurrent design.
- **Paper:** For direct React/Tailwind component synchronization.
- **Diagram-Design:** For automated, publishing-grade HTML+SVG charts.
- **Impeccable v3.5:** For professional design quality enforcement and **Live Mode** sync.
- **Presenton:** For automated "Presentation Orchestration."

## 3. Workflow (Junior Designer Loop)
The Hub follows a progressive disclosure workflow to catch errors early:
1.  **Extract (The Eye):** Capture "Visual DNA" into `DESIGN.md`.
2.  **Verify (Rule Zero):** Perform Fact Verification and execute the **Core Asset Protocol**.
3.  **Sketch:** Iterate on low-fidelity wireframes with placeholders.
4.  **Sync (Layer 1):** Apply `GLOBAL_DESIGN.md` tokens.
5.  **Draft (Layer 2):** Fill with real content using `Stitch` or `Paper`.
6.  **Variations:** Generate 3+ variations (Proactive Orchestration).
7.  **Refine (Skills):** Run `/audit` and `/polish` to eliminate slop.
8.  **Codify:** Sync to React/Tailwind components via `Paper`.
9.  **Live Sync:** Use `Impeccable Live Mode` for final browser-based tuning.
10. **Verify:** Execute `Impeccable /audit` (high-performance reflection).

## 4. File Organization
- Every project MUST have a `DESIGN.md` in its root.
- Every project MUST store `.pen` or `.op` files in a `design/` subdirectory.
- Every project MUST keep visual test logs in `logs/desops.log`.

## 5. Global Token Sync
Use `sync-global-tokens.ps1` in `Atlas\Scripts\DesOps`.

## 6. Future-Proof Principles
- **Orchestration over Creation (Mutagens):** Designing "genetic code" instead of pages.
- **Living Systems Thinking:** Performance informs the `GLOBAL_DESIGN.md`.
- **Zero-Redesign Mandate (Longevity):** Stability is the ultimate aesthetic.

## 7. Meta-Designer Philosophy
The ultimate goal is to transition from "Designing Things" to **"Designing the Systems that Design Things."**

- **Zero-GUI Imperative:** Prioritize terminal-based design workflows.
- **Human-in-the-Loop (Ch. 13):** The Meta-Designer calibrates human intent with machine execution.
- **AI as an Extension:** Freeing the human to focus on strategy and "Visual DNA."
- **Design as a Skill:** Loading expertise as standardized **Agentic Skills**.
- **The New Quotient:** Measurable + Meaningful = Magical.

## 8. Ethics of Aesthetics
- **Aesthetic Responsibility:** Communicating character over mono-aesthetic perfection.
- **Subverting Monoaesthetics:** Intelligence and meanings over empty symmetry.
- **Inclusive Dignity:** Creating spaces that subvert performance-status correlations.

## 9. Agentic Roles (Virtual Functions)
- **Meta-Designer (Leadership):** The Architect of Systems & Steward of Virtue.
- **AI Design Strategist:** The Intelligence Optimizer.
- **Proactive Orchestrator:** Anticipates needs (presentations, variants, audits).
- **Agentic Designer (via Open-Design):** Interchangeable skill-set.
- **Cybernetic Director:** Automates visual brand governance.
- **Sim Designer:** Generates "Synthetic Users" for UX friction detection.
- **Fusionist (Bridge):** Maintains `DESIGN.md` as the unified source of truth.

## 10. Strategic Communication
- **The Arbiter of Taste (Human):** Final curator and manual tuner.
- **Nerdsignalling & Tribal Status:** Signaling depth to carve niche social positions.
- **The OG / Unc Persona:** Credibility through authentic, protocol-driven standards.

## 11. Architectural Performance (Pretext Paradigm)
- **Text-First Layout:** Userland text measurement (chenglou/pretext).
- **Occlusion & Density:** 120fps with hundreds of thousands of elements.

## 12. Foundational Reading
- **Agentic Design Patterns:** antonio Gulli (Google).
- **Hypermedia Systems:** Htmx, pure REST.
- **Type Color:** LaTeX-grade justify.

## 13. Sovereign Hypermedia Architecture (SHA)
- **HDA over SPA:** HTML fragments via `htmx`.
- **Locality of Behavior (LoB):** Logic visible where applied.
- **Uniform Interface (HATEOAS):** Loosely coupled evolution.
- **Thin-Client Sovereignty:** Hyperview (HXML) for mobile shells.
