# Vertekal Resume Builder — Project Tracker

## Overview
A tool for Vertekal leadership to transform raw candidate resumes into polished, Vertekal-formatted resumes designed to capture prime contractor attention and drive interview requests.

**Current Phase:** Phase 1 — Prompt Refinement & Output Quality

---

## Phases

### Phase 1 — Prompt & Output Quality
- [x] Capture existing GPT prompt and guidelines
- [x] Receive example resumes (originals + finished Vertekal versions)
  - Yasin Guergaf: original → finished
  - Sri Kalva: original → finished
- [x] Receive reference resumes (Samuel Martin, Ryan Robertson)
- [x] Analyze patterns across all examples (see below)
- [ ] Run test transformations
- [ ] Iterate until output quality matches expectations
- **Status:** Ready for test runs

### Phase 2 — Word Doc Formatting
- [ ] Receive Vertekal letterhead/branding assets
- [ ] Build .docx generation with exact formatting
- [ ] Match Vertekal's Word template (fonts, spacing, header, layout)

### Phase 3 — Productionize & Deploy
- [ ] Package tool for GitLab repo
- [ ] Name the tool
- [ ] Documentation and usage guide

---

## Resume Formatting Rules (from existing GPT prompt)

### Professional Summary
- Concise, executive-level, results-focused
- Based ONLY on resume content (never invent)
- Highlight: core strengths, key accomplishments, years of experience

### Certifications, Education & Clearance
- Separate sections, each item its own bullet
- Certifications include official PNG logo links

### Professional Experience

**Most Recent 2 Roles:**
- Date format: `YYYY/MM – YYYY/MM` (or `Present`)
- Current role: present tense, **10+ bullets minimum**
- Previous role: past tense, **10+ bullets minimum**
- Bullets: long, detailed, full-row-width for Word
- All company names removed **EXCEPT military branches** (e.g., "U.S. Marine Corps", "United States Air Force")

**Earlier Positions:**
- Past tense only
- **5+ bullets minimum**
- Same quality/detail standards
- All company names removed (same military exception)

### Structure Decisions (confirmed)
- **Flat bullet structure** — no "Tools and Techniques" or "Major Accomplishments" sub-sections
- Tools, technologies, and accomplishments are **interweaved into the experience bullets** themselves
- **No standalone Technical Skills section** — skills are woven into experience bullets
- Follow the Yasin/Sri finished format, NOT the Sam/Ryan sub-sectioned format

### Hard Rules
- Never invent content not present in the resume
- No emojis, casual language, or commentary
- Zero grammar/spelling errors
- Optimized for direct paste into Microsoft Word

---

## Folder Structure
```
resume_builder/
  PROJECT.md              # This file
  examples/
    originals/            # Raw candidate resumes (before)
    finished/             # Vertekal-formatted resumes (after)
    reference/            # Gold-standard resumes (Sam Martin, Ryan Robertson)
```

---

## Notes
- Reference standard: Samuel Martin and Ryan Robertson resumes (some formatting elements will be excluded)
- Previous tool: ChatGPT bot built by Vertekal CTO — output quality has degraded, requiring significant manual rework
