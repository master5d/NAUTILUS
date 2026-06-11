---
name: KRILYB Digitizer
type: pipeline
execution: stateful
description: Automated high-fidelity conversion of yoga manuals to verbatim Markdown ebooks.
---

# 📚 KRILYB Digitizer Skill

This skill implements a robust, automated pipeline to transform legacy Kundalini Yoga manuals (PDF, DOCX, JPG) into "Golden Master" Markdown ebooks. It is optimized for the **NAUTILUS DesOps v3.3** standard and strictly enforces the **Verbatim Mandate**.

## 🚀 Core Features (Inspired by pdf-to-markdown)
- **Verbatim OCR:** Vision-based text extraction that preserves original typos, punctuation, and technical terms.
- **Layout Preservation:** Automatic restoration of centered headers, credits, and page-less continuous flow.
- **Interactive TOC:** Dynamic generation of linked Table of Contents for seamless navigation.
- **Asset Management:** Extraction of original diagrams and insertion of PaperBanana 2.0 SVG rebuilds.
- **Cloud Sync:** Automated deployment to the Google Drive storage layer (`G:\My Drive\KRILYB`).

## 🛠️ Pipeline Stages
1. **Ingest:** Scans `E:\Познание\Телеска Bodywork\Kundalini Yoga\Kundalini Yoga Manuals` for new sources.
2. **Vision-Preproc:** Converts every page to 300dpi PNG for accurate anatomical and textual analysis.
3. **Semantic Rebuild:** Joins paragraphs, removes hard line-breaks, and restores original alignment.
4. **Quality Audit:** Character-by-character comparison against original pixels to ensure 100% truth.
5. **Publish:** Overwrites Golden Master on G-Drive and organizes media assets.

## ⌨️ Usage
- **Process Single File:** `python Atlas/Scripts/Scrapers/krilyb_pipeline.py "path/to/manual.pdf"`
- **Batch Process:** `python Atlas/Scripts/Scrapers/krilyb_pipeline.py --all`
- **Verify Quality:** `python Atlas/Scripts/Scrapers/krilyb_pipeline.py --verify "path/to/manual.md"`

## 🛡️ Mandates
- **Rule 1 (Verbatim Core):** Use ONLY verbatim text. No paraphrasing, summarizing, or modernization of the author's words.
- **Rule 2 (Semantic Enrichment):** You MAY add semantic improvements to the *structure* to enhance readability (e.g., adding technical callouts for Mantras, clearer list formatting, bolding key technical terms, or improving Markdown hierarchy) as long as the underlying text remains 100% identical to the source.
- **Rule 3:** Preserve original typos if they exist in the source.
- **Rule 4:** All headers must be center-aligned via HTML tags for ebook feel.
