---
name: resume
description: "Use this skill when the user wants to generate a Vertekal-branded resume. Triggers include: mention of 'resume', 'candidate resume', 'generate resume', 'transform resume', or providing a raw candidate resume to convert. This skill handles the full pipeline: reading a raw resume, transforming the content per Vertekal standards, and generating a branded .docx file."
---

# Vertekal Resume Generator

Transform a raw candidate resume into a polished, Vertekal-branded .docx resume.

## Workflow

1. **Receive the raw resume** — the user provides a file path to a raw resume (.docx, .pdf, or pasted text)
2. **Read and extract content** from the raw resume
3. **Transform the content** into structured JSON following all Vertekal formatting rules below
4. **Generate the .docx** by running `python3 src/generate_resume.py`

## Step 1: Read the Raw Resume

If the user provides a .docx file, use the docx skill's unpack approach or pandoc to extract text:
```bash
pandoc <input_file> -t plain -o /tmp/resume_raw.txt
```

If they paste text directly, use that.

## Step 2: Transform Content into JSON

Create a JSON file at `examples/input/<candidate_name>.json` with this exact structure:

```json
{
  "name": "Full Name",
  "phone": "(XXX) XXX-XXXX",
  "email": "email@example.com",
  "summary": "...",
  "education": {
    "degree": "Bachelor of Science in ...",
    "university": "University Name"
  },
  "badges": ["csm", "ts_sci", "aws_cloud_practitioner", "security_plus"],
  "jobs": [
    {
      "title": "Job Title",
      "dates": "MM/YYYY – Present",
      "company": null,
      "bullets": ["...", "..."]
    }
  ]
}
```

### Available Badges

Only include badges the candidate actually holds:

| Key | Badge |
|-----|-------|
| `csm` | Certified Scrum Master |
| `ts_sci` | TS/SCI Clearance |
| `aws_cloud_practitioner` | AWS Cloud Practitioner |
| `security_plus` | CompTIA Security+ |

If a candidate has a badge not in this list, omit it (the image won't exist). Flag it to the user so it can be added to `assets/badges/` later.

### Content Transformation Rules

**Professional Summary:**
- Concise, executive-level, results-focused
- Based ONLY on resume content — never invent anything
- Highlight core strengths, key accomplishments, years of experience
- Years of experience should reflect total professional career from earliest role (including military) — maximize without fabricating

**Education & Certifications:**
- Combined into a single section
- Education listed as text (degree, university)
- Certifications represented as badge images (via the `badges` array)
- Clearance represented as the `ts_sci` badge — no text-based clearance statements

**Professional Experience — Most Recent 2 Roles:**
- Date format: `MM/YYYY – MM/YYYY` (or `Present`)
- Current role: present tense, **10+ bullets minimum**
- Previous role: past tense, **10+ bullets minimum**
- Bullets should be long, detailed, and fill the full row width in Word
- Remove ALL company names **EXCEPT military branches** (e.g., "U.S. Marine Corps")
- Set `"company": null` for non-military roles

**Professional Experience — Earlier Positions:**
- Past tense only
- **5+ bullets minimum**
- Same quality and detail standards
- Remove company names (same military exception)

**Short / Low-Value Roles:**
- When multiple roles are brief (a few months) and similar, **combine them into a single role**
- Use a broader job title that encompasses the combined work
- Extend the date range to cover the full span

**Military Roles:**
- **Reframe the job title** to a civilian-equivalent technical title (e.g., "Non-Commissioned Officer" → "Systems Engineer")
- Always **explicitly name the military branch** in the `company` field
- The reframed title should reflect the actual work performed

**Bullet Ordering:**
- Place the most relevant, impactful bullets at the top of each job
- Technical depth and measurable results first
- Soft skills, process, and documentation bullets toward the bottom

**Structure Rules:**
- Flat bullet structure — NO sub-sections like "Tools and Techniques" or "Major Accomplishments"
- Tools, technologies, and accomplishments are woven into the experience bullets
- No standalone Technical Skills section

**Hard Rules:**
- Never invent content not present in the resume
- No emojis, casual language, or commentary
- Zero grammar/spelling errors

## Step 3: Generate the DOCX

```bash
python3 src/generate_resume.py --input examples/input/<candidate_name>.json --output examples/output/<Name>_Vertekal.docx
```

Then open the file for the user to review:
```bash
open examples/output/<Name>_Vertekal.docx
```

## Step 4: Iterate

If the user requests changes, update the JSON file and regenerate. Common tweaks:
- Reorder bullets
- Adjust bullet wording
- Add/remove badges
- Change job titles or dates

## File Locations

| Path | Purpose |
|------|---------|
| `src/generate_resume.py` | DOCX generation script |
| `templates/vertekal_template.docx` | Base template (do not modify) |
| `assets/badges/` | Badge PNG images |
| `examples/input/` | JSON input files |
| `examples/output/` | Generated .docx output |
