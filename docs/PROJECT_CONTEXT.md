# Cytology Workflow Triage Optimizer

## Project Context and Development Guardrails

This document is the authoritative source of truth for the Cytology Workflow Triage Optimizer project.

Any developer, AI assistant, reviewer, or collaborator working on this repository must read this document before recommending or making changes.

When code, terminology, or assumptions appear inconsistent, do not guess. Preserve existing behavior and consult this document first.

---

# 1. Project Purpose

The Cytology Workflow Triage Optimizer is a portfolio project demonstrating how artificial intelligence could improve cytology workflow prioritization after digital slide imaging.

The central problem is:

Traditional cytology worklists are often screened largely in accession order. A potentially high-grade abnormal case may wait behind routine negative cases.

The proposed AI-assisted workflow is:

1. A cytology slide is digitally imaged.
2. An AI model analyzes the digitized slide.
3. The model estimates the probability of abnormal findings.
4. Cases with higher predicted abnormality are moved toward the top of the cytologist worklist.
5. The cytologist screens potentially abnormal cases earlier.
6. Abnormal cases can reach the pathologist earlier.
7. Earlier review may improve turnaround time and increase the possibility of same-day sign out.

The project is not intended to replace cytologist screening or pathologist diagnosis.

The project demonstrates an AI-assisted prioritization layer that helps determine which cases should be reviewed first.

---

# 2. Primary Product Identity

The project is primarily:

**An AI-assisted cytology triage and workflow prioritization system.**

It also includes workflow-routing features that provide clinical context, but the workflow engine must support the AI triage objective rather than replace it.

The project should not drift into becoming a general laboratory information system or a complete laboratory workflow operating system.

The AI triage use case remains the core product concept.

---

# 3. Core Clinical Pain Point

The project is designed to address this specific workflow problem:

## Traditional workflow

* Cases are screened largely in accession order.
* Routine negative cases may be reviewed before potentially abnormal cases.
* A potential HSIL case may wait unnecessarily.
* The case reaches the pathologist later.
* Turnaround time may be longer than necessary.

## AI-assisted workflow

* Slides are digitized after preparation.
* The AI model analyzes the image.
* A potential abnormal case receives a higher abnormality or priority score.
* The case moves higher in the cytologist worklist.
* The cytologist reviews it earlier.
* The case reaches the pathologist earlier when appropriate.
* Earlier final sign out becomes more likely.

Any feature added to the project should support, clarify, demonstrate, or measure this workflow improvement.

---

# 4. Scope and Limitations

This is a portfolio and demonstration project.

It is not:

* A validated medical device
* An FDA-cleared diagnostic system
* A production laboratory information system
* A replacement for cytologist interpretation
* A replacement for pathologist diagnosis
* A clinical decision-making tool
* A production-ready image analysis model

Current predictive features may use simulated or proxy model outputs to demonstrate workflow behavior.

All documentation and user-facing language must clearly distinguish simulated predictive behavior from a validated clinical model.

Do not present simulated predictions as clinically validated AI results.

---

# 5. Critical Terminology Decisions

## ASCUS

Use `ASCUS`, not `ASC-US`.

ASCUS is the terminology selected for this project.

Do not automatically change ASCUS to ASC-US.

---

## Imager Review and Quality Control Review Are Different

This distinction is critical.

### Imager Review

Imager Review evaluates digital imaging quality and imaging-related issues.

Examples include:

* Blur
* Air bubbles
* Stain artifact
* Low cellularity
* Coverslip issues
* Scan failure
* Other image-quality problems

Imager Review occurs before primary cytologist screening when the digital slide requires review or correction.

Internal legacy names may still include `qc`, such as:

* `qc_flag`
* `imager_qc_review`
* `imager_qc_pass`
* `predicted_qc_failure_probability`

These internal names may remain temporarily for backward compatibility.

User-facing labels must use:

* Imager Review
* Imager Review Required
* Imager Review Passed
* Predicted Imager Failure Probability
* Imager Failure Risk

Do not describe Imager Review as cytology quality control rescreening.

### Quality Control Review

Quality Control Review is the regulated or policy-based cytology rescreening process.

For gynecologic cytology, this may include selected negative cases that undergo quality control rescreening.

Quality Control Review is a separate downstream workflow stage.

Do not merge Imager Review with Quality Control Review.

Do not rename one to the other.

Do not use the phrases interchangeably.

---

## Priority Review and Pathologist Review Are Different

The legacy `pathologist_review` attention state is currently used as an operational triage category.

It does not necessarily represent a final clinical routing decision.

User-facing dashboard language should use:

**Priority Review**

when referring to the legacy attention category.

Actual Pathologist Review is a clinical workflow stage determined by specimen type and screening outcome.

Internal legacy values may remain unchanged until a deliberate migration is performed.

Do not rename internal values casually across multiple files.

---

## Concordance and Discrepancy

Use `discrepancy_review`, not `concordance_analysis`, for clinical follow-up terminology.

Discrepancy Review compares preliminary, screening, and final interpretations when appropriate.

Possible discrepancy routes include:

* `no_discrepancy`
* `discrepancy_found`
* `teaching_case`

Educational Review may follow a discrepancy or teaching-case designation.

---

# 6. Specimen and Workflow Categories

The primary specimen categories are:

* `gynecologic`
* `non_gynecologic`

The primary workflow types are:

* `routine`
* `rose`

Do not create a separate FNA workflow type unless there is a clear functional reason.

FNA procedures requiring cytologist attendance are represented through the ROSE workflow.

ROSE is the appropriate workflow for cytologist involvement during an FNA procedure when adequacy assessment is requested.

---

# 7. Clinical Workflow Templates

## Gynecologic Routine Workflow

Base workflow:

1. Specimen received
2. Slide preparation
3. Digital imaging
4. Imager review
5. Primary cytologist screening

Post-screening routing:

### Negative, not selected for quality control

1. Final sign out

### Negative, selected for quality control

1. Quality control review
2. Final sign out

### Abnormal or questionable

1. Pathologist review
2. Final sign out

---

## Non-Gynecologic Routine Workflow

1. Specimen received
2. Slide preparation
3. Digital imaging
4. Imager review
5. Primary cytologist screening
6. Pathologist review
7. Final sign out

---

## ROSE Workflow

1. ROSE procedure
2. ROSE adequacy assessment
3. Laboratory processing
4. Primary cytologist screening
5. Pathologist review
6. Final sign out
7. Discrepancy review, when applicable
8. Educational review, when indicated

Laboratory processing must occur after the ROSE adequacy assessment and before primary cytologist screening.

Laboratory processing may include:

* Cell block preparation
* Cell block sectioning
* Coverslipping ROSE slides
* Monolayer slide preparation
* Other preparation required before screening

Do not remove this processing stage.

---

# 8. AI Triage Behavior

The main prioritization goal is to elevate potentially abnormal cases before cytologist screening.

The worklist should support sorting by AI-derived or simulated abnormality risk.

The recommended priority sort should generally consider:

1. Cases not yet completed
2. Higher AI priority scores
3. Clinical or operational priority
4. Turnaround age

The project should demonstrate that a potentially abnormal case can move ahead of routine negative cases.

Do not allow workflow-routing features to obscure or replace the AI prioritization story.

---

# 9. Predictive Feature Interpretation

Current predictive fields may include:

* `predicted_abnormal_probability`
* `predicted_qc_failure_probability`
* `predicted_turnaround_risk`
* `predicted_risk_score`
* `ai_priority_score`
* `predictive_priority_flag`

User-facing interpretation:

* `predicted_abnormal_probability`: estimated likelihood of an abnormal finding
* `predicted_qc_failure_probability`: predicted imager or image-quality failure risk
* `predicted_turnaround_risk`: predicted risk of turnaround delay
* `ai_priority_score`: combined score used for worklist prioritization
* `predictive_priority_flag`: simplified risk classification

The project must clearly state when these values are simulated, heuristic, synthetic, or proxy outputs.

Do not imply that a deployed image-classification model currently exists unless such a model has actually been implemented and validated.

---

# 10. Database Decisions

The project currently uses SQLite.

The database includes case-level fields such as:

* `case_id`
* `adequacy`
* `scan_status`
* `diagnosis`
* `received_date`
* `reported_date`
* `blur_score`
* `artifact_risk_score`
* `priority`
* `needs_attention`
* `specimen_category`
* `workflow_type`
* `current_stage`
* `screening_result`
* `selected_for_quality_control`
* `discrepancy_review_status`

Database changes must be handled carefully.

Do not use `CREATE TABLE IF NOT EXISTS` as if it automatically migrates an existing table.

When adding columns, verify the schema with:

```bash
sqlite3 data/cytology_workflow.db "PRAGMA table_info(cases);"
```

Do not replace or destroy the database without explicitly confirming that data loss is acceptable.

---

# 11. Streamlit Session Behavior

Some workflow interactions currently use `st.session_state`.

Examples include:

* Temporary case assignment
* Workflow status
* Session activity log
* Demo actions

This behavior is intentional for the current demonstration.

The interface clearly states that these actions do not modify source data.

Do not replace session state with database persistence unless persistence is the explicit next development task.

Do not redesign session behavior without a clear reason.

---

# 12. Internal Backward Compatibility

Some internal names are legacy names.

Examples include:

* `pathologist_review` as an attention state
* `qc_flag`
* `imager_qc_review`
* `imager_qc_pass`
* `predicted_qc_failure_probability`
* `qc_review` as a session workflow status
* `qc_review_cases` in older trend data

These names may remain internally to avoid breaking working code.

User-facing labels should use accurate clinical terminology.

Do not perform broad internal renaming unless:

1. The migration is planned across all affected files.
2. Tests or compile checks are performed.
3. Data files and trend schemas are updated.
4. Backward compatibility is considered.
5. The change solves a real problem.

Avoid cosmetic internal renaming that creates hours of cascading repair work.

---

# 13. Development Guardrails

Before proposing or making a change:

1. Identify the exact defect or objective.
2. Locate every affected reference.
3. Preserve unrelated behavior.
4. Make the smallest safe change.
5. Compile the affected files.
6. Run the dashboard.
7. Confirm the relevant feature works.
8. Stop after the requested change is complete.

Do not combine unrelated cleanup with a functional fix.

Do not redesign large sections of the dashboard while fixing one error.

Do not rename concepts casually.

Do not replace working code solely because another structure appears cleaner.

Do not introduce speculative architecture changes.

Do not move the project away from its AI triage purpose.

---

# 14. Required Verification Commands

After Python changes, run:

```bash
python3 -m py_compile \
    src/dashboard.py \
    src/triage_utils.py \
    src/triage_logic.py \
    src/predictive_features.py \
    src/workflow_engine.py \
    src/database.py
```

When relevant, search for obsolete terminology:

```bash
grep -R \
    "Imager QC Review\|imager QC review\|QC Pass\|Send to QC\|Sent to QC" \
    -n src \
    --exclude-dir="__pycache__"
```

When changing summary keys, verify every reference:

```bash
grep -R "imager_review_pct" -n src --exclude-dir="__pycache__"
```

When changing workflow terminology, verify every reference:

```bash
grep -R \
    "concordance\|discrepancy_review\|educational_review" \
    -n src \
    --exclude-dir="__pycache__"
```

When changing database columns:

```bash
sqlite3 data/cytology_workflow.db "PRAGMA table_info(cases);"
```

Then run:

```bash
streamlit run src/dashboard.py
```

A successful `py_compile` does not guarantee that the Streamlit application will run without runtime errors.

Both checks are required.

---

# 15. Current Development Philosophy

The project should move forward through deliberate, incremental improvements.

The correct approach is:

* One objective at a time
* One small edit at a time
* Verify before continuing
* Preserve working behavior
* Avoid broad rewrites
* Avoid repeated terminology churn
* Avoid unnecessary architecture changes
* Keep the AI triage story central

The goal is progress, not endless cleanup.

---

# 16. Instructions for AI Assistants

Before helping with this project:

1. Read this entire document.
2. Treat it as authoritative.
3. Do not ask the user to restate decisions already documented here.
4. Do not propose changes that conflict with this document.
5. Do not provide a roadmap unless the user asks for one.
6. When the user says they are ready to continue, provide the immediate next coding step.
7. Do not repeat prior background unless it is necessary to explain the next action.
8. When reviewing code, identify the smallest correction needed.
9. Avoid changing multiple files unless required.
10. Preserve clinical terminology.
11. Preserve the distinction between Imager Review and Quality Control Review.
12. Preserve the central AI-assisted triage objective.
13. Do not silently expand the scope of the project.
14. Do not instruct the user to rewrite working files unless necessary.
15. Do not present speculative changes as required work.
16. When uncertain, ask what the current target task is rather than inventing a new direction.
17. After each successful step, provide the next concrete command or code edit.
18. Never make the user reconstruct previous project decisions from memory.

---

# 17. Current Product Statement

The Cytology Workflow Triage Optimizer demonstrates how AI-assisted analysis of digitally scanned cytology slides could prioritize potentially abnormal cases for earlier cytologist screening, while also supporting imager review, clinical workflow routing, turnaround monitoring, and operational reporting.

The core value proposition is:

**Help potentially abnormal cytology cases reach the cytologist and pathologist earlier by intelligently prioritizing the digital worklist.**

---

# 18. Do Not Change Without Explicit Approval

The following decisions require explicit user approval before modification:

* The distinction between Imager Review and Quality Control Review
* The use of ASCUS terminology
* The inclusion of laboratory processing in the ROSE workflow
* The removal of a separate FNA workflow type
* The use of discrepancy terminology
* The core AI triage product purpose
* The use of Streamlit
* The use of SQLite
* The use of session state for demo workflow actions
* The current workflow templates
* The use of simulated predictive outputs for demonstration
* The portfolio and demonstration scope
* Broad renaming of legacy internal fields
* Major dashboard restructuring
* Replacement of the current architecture

---

# 19. Immediate Rule for Future Work

When continuing development, do not begin by summarizing this document.

Begin with:

1. The exact file to edit
2. The exact block to locate
3. The exact replacement or addition
4. The verification command
5. The expected result

Keep each development step small enough to verify before proceeding.
