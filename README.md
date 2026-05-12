# Cytology Workflow Triage Optimizer

AI-assisted cytology workflow triage and cytology QC detection project.


## Current functionality

This project currently reads cytology case data from a CSV file and creates a workflow triage queue.

The tool currently:

- validates required CSV columns
- validates allowed cytology values
- assigns workflow priority based on adequacy, scan status, and diagnosis
- flags cases needing immediate attention
- separates urgent cases from routine workflow
- identifies cases needing pathologist review
- generates summary metrics
- exports triage reports into the results folder

## Current priority logic

1. Unsatisfactory cases
2. Scan failures
3. HSIL
4. LSIL
5. ASCUS
6. Infection
7. Normal