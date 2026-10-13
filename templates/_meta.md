# _meta — where the rules for these docs live

The rules for maintaining this documentation are **not copied here**. Two sources of
truth drift apart, which is the disease the method exists to cure.

Standard: <URL of the standard> — audited against <version> on <date>
<Local working copy, if the standard is also checked out on this machine: the path, marked
as a copy. The URL goes first — a machine-local path means nothing to a reader of the
published project.>
<Local method, only if this project deviates: the folder `workbook-method/` at the
project root. Where the two disagree, the local method wins. Delete this line if there
is no local method.>

The version stamp is what separates "has not caught up with the standard yet" from "was
never kept to it". Those need different responses, and without the stamp they look the
same. Update it when you have actually re-read the standard and brought these documents
into line — not when you happen to edit this file.

| You need | Read |
|----------|------|
| What is mandatory, triggers, session protocol | `RULES.md` of the standard |
| How to format a `G##` / `A##` / `E##`, links, indexes | `FORMATS.md` |
| How to run and record a measurement | `MEASUREMENT.md` |
| Why this project differs from the standard | `DELTA.md` of the local method |

## Project settings

**Profile:** engineering | research
**Tier:** S | M | L — <the number of areas it was counted from. See RULES.md §6>
**Measurement regime** (research only): A (noisy) | B (deterministic)
**Language:** <language of these documents, and when it was decided>. Code identifiers,
file names, JSON keys and log strings stay as they are. Mixing languages inside one
document set is not allowed.

## The three things most often broken here

<A short reminder, not a replacement for RULES.md. Fill in what your project actually
gets wrong — the list is worth rewriting once you know.>

1. <...>
2. <...>
3. <...>

## Checking

```
python tools/lint_workbook.py --docs project-workbook --profile <profile>
```

<Run before every commit through a pre-commit hook, or manually as the last step of a
session if the project is not under version control — and if so, say so, and list which
hard rules are demoted to advice as a result.>
