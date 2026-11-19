---
name: handover-templates
description: Stage-aligned handover document templates written in plain, caveman-friendly language for maximum comprehension. Use when completing any stage (S1-S8), handing off work between agents or teams, documenting security audits, data pipeline status, AI/ML system state, or incident postmortems.
---

# Handover Templates

## Which file should I use?

| Work just finished | Use this file |
|---|---|
| Finished deciding the scope? | `references/S1-domain-scoping-handover.md` |
| Finished planning how parts fit? | `references/S2-architecture-handover.md` |
| Finished making the work list? | `references/S3-task-plan-handover.md` |
| Ready to decide if building starts? | `references/S4-pre-build-gate-handover.md` |
| Finished building? | `references/S5-build-completion-handover.md` |
| Ready to put it live? | `references/S6-deployment-handover.md` |
| Finished checking it? | `references/S7-validation-handover.md` |
| Ready to ship or sell it? | `references/S8-delivery-handover.md` |
| Finished checking safety? | `references/security-audit-handover.md` |
| Finished work on moving data? | `references/data-pipeline-handover.md` |
| Finished work on machine learning? | `references/ai-ml-handover.md` |
| Finished handling a bad event? | `references/incident-postmortem-handover.md` |

## What does each file hold?

- **S1:** Says what we build and why.
- **S2:** Shows how all parts fit.
- **S3:** Lists work, order, time, and owners.
- **S4:** Says if building may start.
- **S5:** Says what builders finished.
- **S6:** Shows how to put work live.
- **S7:** Shows if the work passes checks.
- **S8:** Says if customers can get it.
- **Safety check:** Shows risks, access, and fixes.
- **Data flow:** Shows where data goes.
- **Machine learning:** Shows what the machine part does.
- **Bad event review:** Shows failure, cause, and lessons.

## How do I fill a file?

1. Copy the right file.
2. Keep every question heading.
3. Replace every square-bracket prompt.
4. Use real names and dates.
5. Mark every check with one sign.
6. Remove example blocks before handoff.
7. Run the checker.

Use these prompt shapes:

| Prompt | What to do |
|---|---|
| `[WRITE HERE]` | Put the answer here. |
| `[YES / NO]` | Keep one answer. |
| `[NAME]` | Put a person or team name. |
| `[DATE]` | Put a clear date. |
| `[LINK OR PATH]` | Put the real place. |
| `[NUMBER]` | Put one measured number. |

## How should I write?

- Use tiny words.
- Use short sentences.
- Put one idea in each bullet.
- Explain every short name at once.
- Say what happened.
- Say who owns the next step.
- Use ✅ for done.
- Use ❌ for failed.
- Use ⚠️ for danger.
- Use 🔲 for not checked.
- Never hide a missing answer.

Bad: “Latency breached the service objective.”

Good: “⚠️ The page took four seconds.”

## How do I check the file?

Run:

```bash
python scripts/handover_validator.py --template S1 --file path/to/filled-file.md
```

Use the matching stage name. The checker finds blank prompts. It also finds missing question headings. Fix every gap before handoff.
