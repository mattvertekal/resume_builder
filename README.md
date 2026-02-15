# Vertekal Resume Builder

A Claude Code plugin that transforms raw candidate resumes into polished, Vertekal-branded Word documents.

## Setup

1. Clone this repo into your project directory
2. That's it — the `/resume` skill is available in Claude Code

**Requirements:** Python 3.9+ (no external packages needed)

## Usage

In Claude Code, run:

```
/resume
```

Then provide the path to a raw candidate resume (`.docx`, `.pdf`, or paste the text directly). Claude will:

1. Extract the content from the raw resume
2. Transform it into Vertekal format (summary, bullets, structure)
3. Generate a branded `.docx` with header, footer, badges, and formatting
4. Open it for review

### Example

```
/resume
> Here's the candidate resume: examples/originals/john_doe_resume.docx
```

Output lands in `examples/output/`.

## Manual Usage

If you prefer to run the script directly:

```bash
python3 src/generate_resume.py --input examples/input/candidate.json --output examples/output/Candidate_Vertekal.docx
```

See `examples/input/yasin.json` for the JSON format.

## Available Badges

| Key | Certification |
|-----|--------------|
| `csm` | Certified Scrum Master |
| `ts_sci` | TS/SCI Clearance |
| `aws_cloud_practitioner` | AWS Cloud Practitioner |
| `security_plus` | CompTIA Security+ |

To add a new badge, drop the PNG into `assets/badges/` and update the `BADGE_REGISTRY` in `src/generate_resume.py`.

## Project Structure

```
resume_builder/
  .claude/skills/resume.md      # Claude Code skill definition
  src/generate_resume.py        # DOCX generation engine
  templates/                    # Vertekal branded template
  assets/badges/                # Certification badge PNGs
  examples/
    input/                      # JSON input files
    output/                     # Generated resumes
    originals/                  # Raw candidate resumes
    finished/                   # Reference finished resumes
```
