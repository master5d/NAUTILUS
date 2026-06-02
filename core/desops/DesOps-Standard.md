# DesOps Standard (NAUTILUS)

## 1. The Design Harness (3-Layer Model)
Following the "Design Without Designing" framework, we don't aim to become traditional designers; instead, we implement a design harness that empowers generalists to ship high-end products.

### Layer 1: Skills (The Expertise)
We "borrow taste" from seasoned designers by installing expert logic directly into our AI agents' context.
- **Design Protocols:** We load specific methodologies (e.g., `huashu-design`) as agentic skills. This forces the AI to operate with systemic, "protocol-level" precision instead of generic prompting.
- **Self-Correction Loop:** Agents MUST perform a 5-angle self-audit based on 20+ design principles (governance, contrast, hierarchy, density, alignment) before delivering output. The agent acts as its own harshest critic.
- **Anti-Generic Layer:** Use specialized skills (e.g., `web-design-skill`) to transition from "functional but boring" templates to "exciting and high-density" layouts.
- **Anti-Pattern Guardrails:**
  - ❌ **No Pure Blacks:** Avoid `#000000`. Use deep system grays/blues defined in tokens.
  - ❌ **No Gray-on-Color:** Strictly enforce WCAG contrast for legibility.
  - ❌ **No Nested Cards:** Simplify hierarchy to avoid "AI-generated" cluttered looks.
  - ❌ **Font Overuse:** Stick to the defined Typography Scale.
- **Expert Commands:**
  - `/audit`: Check for accessibility and spacing consistency.
  - `/polish`: Refine alignments, border radii, and subtle shadows. Evaluate "Type Color" and typographic rhythm for LaTeX-level justification.
  - `/delight`: Add micro-interactions and smooth animations.

### Layer 2: Agent Canvas (The Surface)
Design occurs on agent-native surfaces where the AI is the kernel, ensuring no translation layer or handoff.
- **Paper:** Real HTML/CSS canvas for direct component logic.
- **Pencil:** JSON-based `.pen` format for git-diffable, agent-manipulable vector precision.

### Layer 3: The Eye (Visual DNA)
We train our "eye" and the agent's "taste" by absorbing visual DNA from curated sources.
- **Style Dropping:** Use AI to extract color palettes, typographic rhythm, and spatial density from references like Mobbin, Awwwards, and Cosmos.
- **Brand Injection:** Use pre-validated `DESIGN.md` archetypes (e.g., from `awesome-claude-design`) to instantly adopt the visual identity of top-tier products like Stripe, Linear, or Vercel. This eliminates the "generic AI look" and ensures high-end personality from day one.
- **Asset Orchestration (Illustrations):** We avoid static, non-customizable assets. We prioritize modular, SVG-based libraries (e.g., Humaaans, UnDraw, Ouch!) that allow AI agents to programmatically adjust colors and compositions to match the project's tokens.

## 2. Tools & Workflow
- **Stitch / Open-Codesign:** For high-level generative UI and multi-model (BYOK) screen variations.
- **Pencil / OpenPencil:** For vector precision and Git-integrated concurrent design.
- **Paper:** For direct React/Tailwind component synchronization.
- **Diagram-Design:** For automated, publishing-grade HTML+SVG charts and data-dense visuals.
- **Presenton:** For automated "Presentation Orchestration" (Markdown to `.pptx`).
- **Impeccable:** For visual regression testing in CI/CD.

## 3. Workflow (Junior Designer Loop)
The Hub follows a progressive disclosure workflow to catch errors early:
1.  **Extract (The Eye):** Use `Variant` or similar tools to capture "Visual DNA" into `DESIGN.md`.
2.  **Verify (Rule Zero):** Perform Fact Verification and execute the **Core Asset Protocol**.
3.  **Sketch:** Iterate on low-fidelity wireframes or sketches with placeholders.
4.  **Sync (Layer 1):** Ensure `GLOBAL_DESIGN.md` tokens are applied to the sketch.
5.  **Draft (Layer 2):** Fill with real content and branding using `Stitch` or `Paper`.
6.  **Variations:** Proactively generate 3+ variations (Proactive Orchestration).
7.  **Refine (Skills):** Run `/audit` and `/polish` commands to eliminate slop.
8.  **Codify:** Sync to React/Tailwind components via `Paper`.
9.  **Verify:** Execute `Impeccable` visual regression tests.

## 4. File Organization
- Every project MUST have a `DESIGN.md` in its root.
- Every project MUST store `.pen` files in a `design/` subdirectory.
- Every project MUST keep visual test logs in `logs/desops.log`.

## 5. Global Token Sync
To synchronize local project tokens with the global hub, use the `sync-global-tokens.ps1` script located in `Atlas\Scripts\DesOps`.

## 6. Future-Proof Principles
Inspired by the evolving landscape of global design (IDEO, Microsoft, MIT), NAUTILUS adopts these core pillars:

- **Orchestration over Creation (Mutagens):** We don't design pages; we design the "genetic code" (tokens) that generate pages. Our role is to orchestrate the AI to mutate and evolve these forms.
- **Living Systems Thinking:** Design is a learning loop. Every project's UI performance must inform and refine the `GLOBAL_DESIGN.md`.
- **Zero-Redesign Mandate (Longevity):** We prioritize the refinement of the system over the constant churn of newness. Stability and modularity are the ultimate aesthetic.
- **Inclusive Automation (Ethics):** Automated linting MUST include accessibility (WCAG) and neuro-inclusive checks. Design that isn't inclusive is considered "broken" code.
- **Generative Partnership:** We use AI to "shake the tree" of traditional patterns. Humans define the *intent* and *ethos*; machines handle the *flesh* and *scale*.

## 7. Meta-Designer Philosophy
The ultimate goal of DesOps is to transition from "Designing Things" to **"Designing the Systems that Design Things."**

- **Zero-GUI Imperative:** We prioritize terminal-based design workflows where the GUI layer disappears. An 80-point agentic skill in the terminal beats a 100-point browser-based product for high-end engineering efficiency.
- **Managing Complexity:** As design permeates every aspect of the Sovereign Mesh, the Meta-Designer ensures total consistency and coherence across all project touchpoints.
- **AI as an Extension:** We don't just use AI; we integrate it. The Meta-Designer builds the harness that enables AI to automate the mundane, freeing the human to focus on strategy and "Visual DNA."
- **Design as a Skill:** We move from "Design as a Profession" to **"Design as a Loadable Skill."** Our agents (Claude Code, Cursor) load design-specific expertise (via `open-design` or `huashu-design`) on-demand, rendering "we have no designer" a legacy constraint.
- **Future-Proofing:** Anticipating shifts in technology (like the move to Hypermedia or Text-First Layouts) and proactively adapting the system's objectives.
- **Cross-Disciplinary Unity:** The Meta-Designer acts as the bridge between Engineering, Art, and Strategy, ensuring a unified and user-centered Sovereign experience.

## 8. Agentic Roles (Virtual Functions)
The DesOps Hub abstracts complex human design roles into automated AI functions, overseen by the Meta-Designer:

- **Meta-Designer (Leadership):** The Architect of Systems. Designs the processes, tools, and objectives that guide the Hub.
- **AI Design Strategist:** Strategizes how to leverage AI/ML to enhance the design harness.
- **Proactive Orchestrator:** An autonomous function that anticipates needs (e.g., generating presentations, variants, or audits) before being asked, based on project context.
- **Agentic Designer (via Open-Design):** An interchangeable skill-set loaded into code agents. Provides 30+ design skills, 70+ brand systems, and sketch-to-prototype logic.
- **Cybernetic Director:** Automates visual brand governance.
- **Sim Designer:** Generates "Synthetic Users" to simulate interaction flows and detect UX friction before production.
- **Fusionist (Bridge):** Maintains the `DESIGN.md` as the unified bridge between Engineering (Tokens), Art (Rationales), and Business (Principles).

## 9. Strategic Communication
Architecture and design decisions MUST be communicated effectively to varied audiences:

- **The Arbiter of Taste (Human):** The final curator. Manages the "mix-and-match" process of AI variants and provides the final high-fidelity "manual tuning."
- **For Stakeholders (Business):** Focus on the *Why* and the *Outcome*. Use the `Rationale` and `Ethos` sections of `DESIGN.md` to explain how design supports business goals (Longevity, Ethics, Efficiency).
- **For Developers (Engineering):** Focus on the *How* and the *Contract*. Provide precise YAML tokens, component specs, and anti-pattern guardrails.
- **For Users (Product):** Focus on the *Experience*. Use "Synthetic UX Audit" results to demonstrate usability and accessibility.
- **Unified Narrative:** The `DESIGN.md` serves as the primary communication artifact, ensuring that regardless of the audience, the core "Design DNA" remains consistent and transparent.

## 10. Architectural Performance (Pretext Paradigm)
We don't settle for standard DOM limitations. For data-dense NAUTILUS UIs (like Nooscope):

- **Text-First Layout:** Leverage the principles of `@chenglou/pretext` for high-performance userland text measurement. Bypass expensive browser reflows for complex, dynamic layouts.
- **Occlusion & Density:** Prioritize virtualization/occlusion to maintain 120fps while handling hundreds of thousands of elements. Performance is a feature, not a byproduct.
- **AI-Native Engineering:** Use agents (Claude Code, Codex) to iterate against "ground truth" browser measurements for foundational UI logic.

## 11. Foundational Reading
- **Hypermedia Systems:** Design systems should prioritize the hypermedia constraint (Htmx, pure REST) for maximum sovereignty and minimal client-side bloat.
- **Type Color:** Aim for uniform spatial density in typographic blocks to ensure high legibility and "journalistic gravitas."

## 12. Sovereign Hypermedia Architecture (SHA)
To ensure maximum autonomy and minimal "JS Fatigue," NAUTILUS projects follow the Hypermedia Paradigm:

- **HDA over SPA:** Prioritize Hypermedia-Driven Applications. Use `htmx` to swap HTML fragments instead of managing complex JSON-to-Client state synchronization. The Server is the source of truth for both Data and Application State.
- **Locality of Behavior (LoB):** Logic must be visible where it is applied. Avoid global "app.js" files; use inline `hx-` attributes and localized scripting (e.g., Alpine.js) to keep components self-contained.
- **Uniform Interface (HATEOAS):** The client should only understand Hypermedia (HTML/HXML). Server responses must contain the next possible actions, ensuring the system is Loosely Coupled and evolves without client-side updates.
- **Thin-Client Sovereignty:** Mobile apps MUST prioritize `Hyperview` (HXML) to act as thin shells. This enables instant UI updates directly from the Sovereign Server, bypassing App Store review cycles for non-logic changes.
