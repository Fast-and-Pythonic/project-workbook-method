#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Documentation linter for the Project Workbook standard.
#
# Implements the checks specified in RULES.md ("What lint checks"). Every check backs a
# hard rule there, or catches rot that has actually happened in the projects this
# standard came from.
#
#   python tools/lint_workbook.py --docs project-workbook --profile engineering
#
# Exit code 0 = clean (warnings allowed), 1 = at least one error.
#
# Configuration lives in lint_workbook.toml beside this file; every value has a default, so
# the linter runs on a project that has no config at all. Command-line flags win over
# the config file.

import argparse
import fnmatch
import json
import os
import re
import sys
from collections import Counter

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None


# --- configuration ------------------------------------------------------------------

DEFAULTS = {
    "paths": {
        "root": ".",
        "docs": "project-workbook",
        "method": "workbook-method",
        "corpus": "project-workbook/corpus.md",
        "baseline": "",
        "extra_doc_dirs": [],
        # Directories inside docs/ where register entries may live once a register has
        # been split by area (RULES.md, "Scaling"): the register file keeps the index,
        # the bodies move under these. Empty means every register is a single file.
        "register_bodies": [],
        # Prefixes a local method numbers its departures with. `D` is the standard's own
        # (DEVIATIONS.md), but a project that borrowed some departures from a sibling and
        # added others of its own numbers the two apart — and the borrowed ones collapse
        # when they are promoted, so renumbering the rest would break live links.
        "delta_prefixes": ["D"],
        "path_roots": ["", "project-workbook"],
        # Directories never searched when resolving a documented path. Generated trees
        # are orders of magnitude larger than the source they come from, and a path that
        # resolves only inside one is not evidence that the documented file exists.
        "ignore_dirs": [".git", "node_modules", "build", "target", "dist", ".cxx",
                        ".gradle", ".idea", "__pycache__", "venv", ".venv"],
        "root_pointers": ["AGENTS.md", "CLAUDE.md", ".cursorrules",
                          ".github/copilot-instructions.md"],
        # The file for a person joining the project: what works with nothing installed,
        # what to install, what to enable in their agent (check 21). "" turns it off, for
        # a document set nobody else will ever join.
        "onboarding": "ONBOARDING.md",
        "allow": [],
    },
    "profile": {"name": "engineering"},
    # Size tier: "S", "M" or "L". It adjusts the limits below and the expected inventory,
    # and nothing else — see RULES.md, "Tiers and scaling".
    "project": {"tier": "S"},
    "registers": {"G": "gotchas.md", "A": "architecture.md", "E": "experiments.md"},
    "limits": {
        "start.md": 150,
        "status.md": 150,
        # Pages grow by design; past this they warn "split the page", not "stop writing".
        "subsystems/*.md": 300,
        "references/*.md": 300,
        "register_split_warn": 60,
        # Which limits are errors. Only a limit that *forces* something belongs here —
        # status.md's exists to refuse a chronicle, not to save bytes. Every other limit
        # warns: it says "this is getting long", which is advice, and an error there is
        # a linter crying wolf.
        "enforce": ["status.md"],
    },
    "numbers": {
        "result_files": ["status.md", "journal.md", "experiments.md", "overview.md"],
        "units": ["ms", "MB/s", "fps", "%", "s"],
        # A figure does not stop being a measurement because its unit was left off:
        # "p50 fell from 33.70 to 31.02" is invisible to a unit-based pattern. A metric
        # name next to a decimal is treated the same as a number with a unit. List the
        # metric names your project actually reports.
        "metric_names": ["p50", "p95", "p99", "frametime"],
        # Legitimate exceptions. Each should carry, in the config, the reason it is not
        # a traceable measurement — a threshold, a run setting, a stated target.
        "allow": ["acceptance criterion", "threshold"],
    },
    "measurement": {
        "required_fields": ["corpus_id", "experiment", "compare_to", "run_order"],
        "id_field": "corpus_id",
        # Prefix used in [[<prefix>:<id>]] links to a run configuration. Projects that
        # measure something other than a corpus name it differently — "scene", "dataset".
        "link_prefix": "corpus",
        # Directory name holding the raw reports a baseline was curated from. They are
        # inputs, not stored measurements, and older ones predate the schema.
        "raw_dir": "raw",
    },
    # Field labels as they appear in the documents. The standard is written in English,
    # but a project may keep its documents in another language (METHODOLOGY.md, section
    # 5). Hard-coding the English labels would silently disable half the research checks
    # on such a project — they would find no Prediction block and no Status line, and
    # report nothing.
    "labels": {
        "prediction": "Prediction",
        "status": "Status",
        "status_open": "open",
        "status_refuted": "refuted",
        # A prediction reconstructed after the run. The marker exists because nothing can
        # verify that such a prediction was not fitted to the outcome, which is also why
        # it is not held to the "name a quantity" bar — see check_predictions.
        "status_retro": "retro",
        "acceptance_criterion": "Acceptance criterion",
        # The line in _meta.md that names the standard these documents are kept to.
        "standard": "Standard",
    },
    "tasks": {
        # Shape of a task id, e.g. T-1, I-2, R-2ab.
        "id_pattern": r"[A-Z]-[0-9a-z]+",
        "backlog": "plan/backlog.md",
        "plan_dir": "plan",
        # The line in backlog.md that declares which statuses are legal.
        "legend_label": "Status legend:",
    },
}

RESEARCH_ONLY = {"E"}  # registers that exist only in the research profile

TIERS = ("S", "M", "L")

# Limits a tier moves. Only what a larger project legitimately needs more of appears
# here. Tier L had status.md at 120 until 2026-10, when the common limit rose to 150
# and made it moot. Anything a project sets explicitly under [limits] wins over these.
TIER_LIMITS = {
    "S": {},
    "M": {},
    "L": {},
}

# Files expected from a given tier upward (RULES.md §1, the Tier column). Below its tier
# a file is unwarranted rather than missing, which is the half of the rule that lets a
# small project stay small.
TIER_INVENTORY = {
    "M": ["journal.md"],
}


def load_config(path, overrides):
    cfg = {k: dict(v) if isinstance(v, dict) else v for k, v in DEFAULTS.items()}
    # Which keys the project set for itself, so a tier default never silently overrides
    # a deliberate choice. Defaults and tiers fill gaps; they do not compete.
    explicit = {}
    if path and os.path.exists(path):
        if tomllib is None:
            print("warning  Python < 3.11: cannot read lint_workbook.toml, using defaults "
                  "and command-line flags only")
        else:
            with open(path, "rb") as f:
                for section, values in tomllib.load(f).items():
                    if section == "registers":
                        # The set of registers is a whole, not a list of overrides: a
                        # document set with its own prefixes must be able to drop the
                        # default ones, or G/A/E keep being looked for where they
                        # never existed.
                        cfg[section] = dict(values)
                    elif isinstance(values, dict):
                        cfg.setdefault(section, {}).update(values)
                        explicit.setdefault(section, set()).update(values)
                    else:
                        cfg[section] = values
            cfg["_config_path"] = path
    for section, key, value in overrides:
        if value is not None:
            cfg.setdefault(section, {})[key] = value
            explicit.setdefault(section, set()).add(key)

    tier = str(cfg.get("project", {}).get("tier", "S")).upper()
    if tier not in TIERS:
        print(f"warning  unknown tier {tier!r}, treating the project as S; "
              f"valid tiers are {', '.join(TIERS)}")
        tier = "S"
    cfg.setdefault("project", {})["tier"] = tier
    for name, limit in TIER_LIMITS[tier].items():
        if name not in explicit.get("limits", ()):
            cfg["limits"][name] = limit
    return cfg


# --- state --------------------------------------------------------------------------

errors, warnings = [], []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


class Ctx:
    """Resolved paths and patterns for one run. Built once in main()."""

    def __init__(self, cfg):
        p = cfg["paths"]
        self.cfg = cfg
        self.research = cfg["profile"]["name"] == "research"
        self.root = os.path.abspath(p["root"])
        self.docs = self._abs(p["docs"])
        self.method = self._abs(p["method"]) if p.get("method") else None
        self.corpus = self._abs(p["corpus"]) if p.get("corpus") else None
        self.baseline = self._abs(p["baseline"]) if p.get("baseline") else None
        self.extra_doc_dirs = [self._abs(d) for d in p.get("extra_doc_dirs", [])]
        self.register_bodies = [os.path.normpath(os.path.join(self.docs, d))
                                for d in p.get("register_bodies", [])]
        self.delta_prefixes = list(p.get("delta_prefixes", ["D"])) or ["D"]
        self.path_roots = [self._abs(r) for r in p.get("path_roots", [])]
        self.ignore_dirs = set(p.get("ignore_dirs", []))
        self._tree = None  # built on first use; see known_paths()
        self.path_allow = set(p.get("allow", []))
        self.tier = cfg.get("project", {}).get("tier", "S")
        self.root_pointers = [self._abs(f) for f in p.get("root_pointers", [])]
        self.onboarding = self._abs(p["onboarding"]) if p.get("onboarding") else None

        self.registers = {k: os.path.join(self.docs, v)
                          for k, v in cfg["registers"].items()
                          if self.research or k not in RESEARCH_ONLY}

        t = cfg["tasks"]
        self.task_re = re.compile(rf"^\| ({t['id_pattern']}) \|", re.MULTILINE)
        self.task_shape = t["id_pattern"]
        self.backlog = os.path.join(self.docs, t["backlog"])
        self.plan_dir = os.path.join(self.docs, t["plan_dir"])
        self.legend_label = t["legend_label"]
        self.link_prefix = cfg["measurement"]["link_prefix"]

        lb = cfg["labels"]
        self.labels = lb
        # A label may carry a qualifier — "Prediction (reconstructed)" — so match the
        # word and allow anything up to the closing bold marker.
        self.prediction_block_re = re.compile(
            rf"^\*\*{re.escape(lb['prediction'])}[^*]*\*\*.*?(?=^\*\*|\Z)",
            re.DOTALL | re.MULTILINE)
        self.prediction_field_re = re.compile(
            rf"\*\*{re.escape(lb['prediction'])}[^*]*\*\*(.*?)(?:\n\*\*|\Z)",
            re.DOTALL)
        self.status_open_re = re.compile(
            rf"\*\*{re.escape(lb['status'])}:\*\*\s*{re.escape(lb['status_open'])}")
        self.status_refuted_re = re.compile(
            rf"\*\*{re.escape(lb['status'])}:\*\*\s*{re.escape(lb['status_refuted'])}")
        self.status_retro_re = re.compile(re.escape(lb.get("status_retro", "retro")))
        self.criterion_label = lb["acceptance_criterion"]

        n = cfg["numbers"]
        units = "|".join(re.escape(u) for u in n["units"])
        self.number_re = re.compile(rf"\b\d+(?:[.,]\d+)?\s*({units})\b")
        metrics = "|".join(re.escape(m) for m in n["metric_names"])
        self.metric_re = re.compile(rf"\b({metrics})\b", re.IGNORECASE) if metrics \
            else re.compile(r"(?!)")
        self.number_allow = n["allow"]

        self.config_path = cfg.get("_config_path")
        self.limits = cfg["limits"]
        self.split_warn = int(self.limits.get("register_split_warn", 60))
        self.enforced_limits = set(self.limits.get("enforce", ["status.md"]))

    def _abs(self, rel_path):
        # "" means the root itself — a legitimate entry in path_roots, and not the
        # same thing as an unset optional path.
        if rel_path is None:
            return None
        return os.path.normpath(os.path.join(self.root, rel_path))

    def rel(self, path):
        return os.path.relpath(path, self.root).replace("\\", "/")


# --- shared patterns ----------------------------------------------------------------

BARE_NUMBER_RE = re.compile(r"\b\d+\.\d+\b")
# A real path ending in .json, not merely the substring ".json" somewhere in the
# paragraph — the loose version was trivially satisfiable.
JSON_REF_RE = re.compile(r"[\w./\\-]+\.json")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)")
# Where a path with spaces ends is ambiguous in prose, so the convention is: an absolute
# path in prose must be inside backticks, and then it may contain spaces. A bare path is
# only recognised when it has none. Fenced blocks are skipped — they hold examples.
ABS_PATH_BARE_RE = re.compile(r"[A-Za-z]:\\[^\s`'\"<>|)]+")
ABS_PATH_TICKED_RE = re.compile(r"`([A-Za-z]:\\[^`\n]+)`")
# A repo-relative path in backticks: at least one slash and a file extension. The slash
# separates a path from a bare file name, which is a name and not a location.
REL_PATH_RE = re.compile(r"`([\w.][\w./-]*/[\w./-]*\.[\w]{1,6})`")
PATH_PLACEHOLDER_CHARS = "<>*{}#"
# Acceptance criteria that hedge instead of stating a number. A warning: some criteria
# are legitimately qualitative, but "noticeably better" is not one.
HEDGE_RE = re.compile(r"\b(noticeably|measurable|faster than|better than|more steadily"
                      r"|significantly|substantially)\b", re.IGNORECASE)
# The lead-in a generator writes into every Prediction block; it cannot count as one.
BOILERPLATE_BULLET_RE = re.compile(r"Threshold:\s*computed by", re.IGNORECASE)


def md_files(base, skip=()):
    if not base or not os.path.isdir(base):
        return
    skip = [os.path.normpath(s) for s in skip if s]
    for dirpath, dirs, names in os.walk(base):
        # A method folder nested inside the docs (a document set that is itself a
        # repository root has nowhere else to put one) holds placeholders such as
        # [[E##]]; walked as docs, every one of them reads as a broken link.
        dirs[:] = [d for d in dirs
                   if os.path.normpath(os.path.join(dirpath, d)) not in skip]
        for n in sorted(names):
            if n.endswith(".md"):
                yield os.path.join(dirpath, n)


def docs_files(ctx):
    """Markdown under docs/, minus a method folder nested inside it."""
    return md_files(ctx.docs, skip=[ctx.method])


def read(path):
    # utf-8-sig, not utf-8: a BOM is a no-op for the first but survives into the string
    # for the second, where it lands before the first character of the first line. Every
    # check anchored with ^ or startswith then misses on line 1 only — so a _meta.md
    # saved by a Windows editor reported "no Standard line" while the line was plainly
    # there. A wrong diagnosis costs more than a missing one.
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def strip_code(text):
    """Drop fenced blocks and HTML comments — both hold examples, not live content.

    Comments matter as much as fences here: a template ships its entry skeleton inside
    one, and without this the linter reads the skeleton as a real entry — reporting a
    freshly-copied template as broken, and making the experiment tool allocate E02 for
    the first experiment in a project.
    """
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def linted_docs(ctx):
    """Every markdown the linter is responsible for."""
    paths = list(docs_files(ctx))
    paths += list(md_files(ctx.method))
    for d in ctx.extra_doc_dirs:
        paths += list(md_files(d))
    paths += [f for f in ctx.root_pointers if os.path.exists(f)]
    return paths


def known_paths(ctx):
    """Every file under the root, as forward-slash paths relative to it.

    Built once, on first use, and skipping the generated trees named in ignore_dirs —
    without that skip this walks an order of magnitude more files than the project has,
    and resolves documented paths against build output.
    """
    if ctx._tree is None:
        found = set()
        for dirpath, dirs, names in os.walk(ctx.root):
            dirs[:] = [d for d in dirs if d not in ctx.ignore_dirs]
            rel = os.path.relpath(dirpath, ctx.root)
            prefix = "" if rel == "." else rel.replace("\\", "/") + "/"
            for n in names:
                found.add(prefix + n)
            for d in dirs:
                found.add(prefix + d)
        ctx._tree = found
    return ctx._tree


def resolve_rel_path(ctx, token, doc_dir):
    """True if a documented repo-relative path points at something that exists.

    Two stages, and the second is what the error message has always promised. A path is
    first tried against the declared roots — exact, cheap, and the common case. Failing
    that, it is looked for as the tail of any path in the tree: documentation refers to
    `model/Screen.kt` or `res/xml/file_paths.xml` the way a person does, from whichever
    source root the reader is expected to have in mind, and demanding the full
    `app/src/main/java/com/example/model/Screen.kt` in prose is a demand nobody meets.

    Suffix matching is deliberately generous. The check exists to catch a documented path
    that points at nothing — a file that was renamed or deleted. It is not a check that
    the path is written canonically, and treating it as one produced twelve false errors
    against four real ones on the first large project it met, which is how a linter
    teaches a session to stop reading its output.
    """
    for root in ctx.path_roots + [doc_dir]:
        if os.path.exists(os.path.join(root, token)):
            return True
    token = token.strip("/")
    if not token:
        return False
    tail = "/" + token
    return any(p == token or p.endswith(tail) for p in known_paths(ctx))


# --- inventories --------------------------------------------------------------------

def register_entries(ctx, prefix):
    """Every entry of a register: id -> list of (file, title).

    Bodies live in the register file itself and, once the register has been split by
    area, in any markdown under `register_bodies`. A list rather than a single file
    because the same id in two files is a defect this has to be able to report.
    """
    path = ctx.registers[prefix]
    files = [path] if os.path.exists(path) else []
    for d in ctx.register_bodies:
        files += [f for f in md_files(d, skip=[ctx.method])
                  if os.path.normpath(f) != os.path.normpath(path)]
    entries = {}
    for f in files:
        text = strip_code(read(f))
        for eid, title in re.findall(rf"^## ({prefix}\d+)\s*[.:] ?(.*)$", text,
                                     re.MULTILINE):
            entries.setdefault(eid, []).append((f, title))
    return entries


def register_index(ctx, prefix):
    """The index of a register: id -> (title remainder, section file or None).

    An index may be grouped under headings that link to the file holding that area's
    bodies — `## Windows — [environments/windows.md](environments/windows.md)`. The
    file is recorded per line so the linter can hold the index to it.
    """
    path = ctx.registers[prefix]
    if not os.path.exists(path):
        return {}
    index, section = {}, None
    for line in strip_code(read(path)).splitlines():
        if line.startswith("## "):
            m = MD_LINK_RE.search(line)
            section = None
            if m and m.group(1).endswith(".md"):
                section = os.path.normpath(
                    os.path.join(os.path.dirname(path), m.group(1)))
            continue
        m = re.match(rf"^- \*\*({prefix}\d+)\*\*(.*)$", line)
        if m:
            index[m.group(1)] = (m.group(2), section)
    return index


def register_ids(ctx, prefix):
    return set(register_entries(ctx, prefix)), set(register_index(ctx, prefix))


def task_ids(ctx):
    if not os.path.exists(ctx.backlog):
        return set()
    return set(ctx.task_re.findall(strip_code(read(ctx.backlog))))


def corpus_ids(ctx):
    if not ctx.corpus or not os.path.exists(ctx.corpus):
        return set()
    return set(re.findall(r"^## ([a-z0-9][a-z0-9-]*)\s*$", strip_code(read(ctx.corpus)),
                          re.MULTILINE))


def delta_ids(ctx):
    if not ctx.method:
        return set()
    path = os.path.join(ctx.method, "DELTA.md")
    if not os.path.exists(path):
        return set()
    prefixes = "|".join(re.escape(p) for p in
                        sorted(ctx.delta_prefixes, key=len, reverse=True))
    return set(re.findall(rf"^## ((?:{prefixes})\d+)\.", strip_code(read(path)),
                          re.MULTILINE))


# --- checks -------------------------------------------------------------------------

def known_shape_re(ctx):
    """An id of one of these shapes is expected to exist.

    Failing to resolve one is a typo, not a forward reference, so it is an error
    (rule H2). Corpus ids and subsystem pages are the exception — those are
    legitimately referenced before they exist.
    """
    # An alternation, longest first, not a character class: a class would read a
    # two-letter prefix such as EG as "E or G" and never match [[EG07]].
    prefixes = "|".join(sorted(ctx.registers, key=len, reverse=True))
    deltas = "|".join(re.escape(p) for p in
                      sorted(ctx.delta_prefixes, key=len, reverse=True))
    return re.compile(rf"^(?:(?:{prefixes})\d+|(?:{deltas})\d+|{ctx.task_shape})$")


def check_links(ctx, known):
    """1. Broken [[links]] and broken markdown links to files."""
    shape = known_shape_re(ctx)
    targets = list(docs_files(ctx))
    if ctx.corpus and os.path.exists(ctx.corpus):
        targets.append(ctx.corpus)
    # [[wikilinks]] only in the docs: a method folder holds placeholders like [[E##]]
    # that are samples. Its *file* links are checked below all the same — a rotting path
    # there is no less broken for living in the method folder.
    for path in targets:
        text = strip_code(read(path))
        for target in WIKILINK_RE.findall(text):
            if target in known:
                continue
            if target.startswith("subsystems/"):
                if not os.path.exists(os.path.join(ctx.docs, target + ".md")):
                    warn(ctx.rel(path),
                         f"[[{target}]] — subsystem page does not exist yet")
            elif target.startswith(ctx.link_prefix + ":"):
                warn(ctx.rel(path),
                     f"[[{target}]] — configuration not registered in the corpus")
            elif shape.match(target):
                err(ctx.rel(path),
                    f"[[{target}]] — looks like an id but resolves to nothing")
            else:
                warn(ctx.rel(path), f"[[{target}]] — does not resolve to any known entry")

    for path in linted_docs(ctx):
        for target in MD_LINK_RE.findall(strip_code(read(path))):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                err(ctx.rel(path), f"broken link -> {target}")


STOPWORDS = {"with", "that", "this", "from", "into", "when", "does", "have", "than"}


def significant_words(s):
    # Letters of any script, not [a-z]: an ASCII-only pattern matches nothing in a
    # document set written in Russian, Greek or Japanese, so every index line "shares
    # no words" with its heading and the check fires on every entry in the file.
    return {w for w in re.findall(r"[^\W\d_]{4,}", s.lower())} - STOPWORDS


def check_index_titles(ctx, path, entries, index):
    """3. An index line that shares nothing with its entry's heading.

    A warning, not an error: titles are prose and may legitimately be reworded. But an
    index line describing something else entirely is how an index quietly stops being a
    map of the file.
    """
    # Index lines differ in shape between registers (gotchas carry a title, experiments
    # carry status and task too), so take the whole remainder of the line and test for
    # any overlap rather than trying to parse fields out of it.
    for eid, (title, _) in index.items():
        if eid not in entries:
            continue
        heading = entries[eid][0][1]
        if heading and not (significant_words(title) & significant_words(heading)):
            warn(ctx.rel(path), f"{eid}: index line and heading share no words — "
                                f"'{title.strip()[:40]}' vs '{heading.strip()[:40]}'")


def check_index_sections(ctx, path, entries, index):
    """17. An index grouped by file: every id sits under the section of its own file.

    Only fires when the index has sections that link to a file; a flat index has
    nothing to hold it to. This is what breaks when an entry moves between the files
    of a split register and the index is not updated to match.
    """
    for eid, (_, section) in index.items():
        if section is None or eid not in entries:
            continue
        actual = os.path.normpath(entries[eid][0][0])
        if actual != section:
            err(ctx.rel(path), f"{eid} is indexed under the section for "
                               f"{ctx.rel(section)} but its entry is in "
                               f"{ctx.rel(actual)}")


def check_registers(ctx):
    """2. Index against headings, and gaps in numbering."""
    for prefix, path in ctx.registers.items():
        if not os.path.exists(path):
            continue
        entries, index_lines = register_entries(ctx, prefix), register_index(ctx, prefix)
        headings, index = set(entries), set(index_lines)
        for eid, places in sorted(entries.items()):
            if len(places) > 1:
                err(ctx.rel(path), f"{eid} has an entry in more than one file: "
                                   + ", ".join(ctx.rel(f) for f, _ in places))
        # A register holding numbered entries under some other scheme — "## 7. Something"
        # instead of "## G07. Something" — parses as empty, and every check below then
        # passes by finding nothing, which reads as approval. Tested on the numbering
        # rather than on file length: a register created ahead of its first entry, with
        # an explanatory preamble, is legitimate and must stay quiet.
        if not headings and not index:
            foreign = re.findall(r"^## (\d+|[A-Z]{1,2}\d+)\s*[.:]",
                                 strip_code(read(path)), re.MULTILINE)
            if foreign:
                warn(ctx.rel(path),
                     f"{len(foreign)} numbered entries, none of them {prefix}## — "
                     f"entries are headed '## {prefix}01. Title'. A register in another "
                     f"format is silently not checked at all")
            continue
        # A register with entries and no index at all is one defect, not one per entry.
        # Reporting it forty times buries everything else in the run.
        if headings and not index:
            err(ctx.rel(path), f"{len(headings)} entries and no index — a growing "
                               f"register opens with one line per entry, or it cannot "
                               f"be surveyed without reading it whole")
        else:
            for missing in sorted(headings - index):
                err(ctx.rel(path), f"{missing} has an entry but no index line")
            for missing in sorted(index - headings):
                err(ctx.rel(path), f"{missing} is indexed but has no entry")
        check_index_titles(ctx, path, entries, index_lines)
        check_index_sections(ctx, path, entries, index_lines)
        nums = sorted(int(i[len(prefix):]) for i in headings)
        if nums and nums != list(range(1, len(nums) + 1)):
            gaps = sorted(set(range(1, max(nums) + 1)) - set(nums))
            err(ctx.rel(path), f"gap in {prefix}## numbering: {gaps} — a deleted entry?")


def check_register_size(ctx):
    """8. A register grown past the point where its index is still scannable.

    Once the register has been split by area, the total no longer means anything —
    splitting is the answer to it, and it keeps growing afterwards. The threshold then
    applies to each file that holds bodies, and the warning names the area to split.
    """
    for prefix, path in ctx.registers.items():
        if not os.path.exists(path):
            continue
        entries = register_entries(ctx, prefix)
        if not ctx.register_bodies:
            if len(entries) > ctx.split_warn:
                warn(ctx.rel(path), f"{len(entries)} entries (over {ctx.split_warn}) — "
                                    f"time to split the register by area; see 'Scaling' "
                                    f"in RULES.md")
            continue
        per_file = {}
        for occurrences in entries.values():
            for f, _ in occurrences:
                per_file[f] = per_file.get(f, 0) + 1
        for f, n in sorted(per_file.items()):
            if n > ctx.split_warn:
                warn(ctx.rel(f), f"{n} {prefix}## entries in this area (over "
                                 f"{ctx.split_warn}) — time to split the area; see "
                                 f"'Scaling' in RULES.md")


def check_line_limits(ctx):
    """4. Line limits, as errors where a limit forces something and warnings elsewhere.

    Only a *forcing* limit is an error, and `limits.enforce` names them. The one that
    earns it is status.md: its job is to refuse an append-only chronicle, so that the
    chronicle goes to journal.md instead of crowding out the state nobody can then find.
    That is a claim about structure, not about size — measured across six document sets,
    everything a session always reads comes to about 6k tokens, so no limit here is
    defending a context budget.

    Everything else warns: a glob (`subsystems/*.md`) covers files that grow by design,
    and a plain name outside `enforce` says "this is getting long", which is advice. An
    error for advice is a linter crying wolf, and the next session stops reading it.
    """
    for name, limit in ctx.limits.items():
        if name in ("register_split_warn", "enforce"):
            continue
        if any(c in name for c in "*?["):
            paths = [p for p in docs_files(ctx)
                     if fnmatch.fnmatch(
                         os.path.relpath(p, ctx.docs).replace("\\", "/"), name)]
            forcing = False
        else:
            paths = [os.path.join(ctx.docs, name)]
            forcing = name in ctx.enforced_limits
        for path in paths:
            if not os.path.exists(path):
                continue
            n = len(read(path).splitlines())
            if n > int(limit):
                if forcing:
                    err(ctx.rel(path), f"{n} lines, limit {limit}")
                else:
                    warn(ctx.rel(path), f"{n} lines, over the limit of {limit} "
                                        f"— advisory, not a defect")


def check_limit_overrides(ctx):
    """20. Every limit a project overrides carries its reason, and differs from the default.

    Measured before this check existed: across nine document sets the same default had
    been overridden to the same value in five configs, and to stale values in two — a
    status.md limit raised for a table that had since moved out. An override nobody can
    explain is one nobody dares remove, so the defaults stop meaning anything. A comment
    on the line, or on the lines right above it, is the reason; the check cannot judge
    the reason, only that one was written. Warnings: this is housekeeping, not a defect.
    """
    if not ctx.config_path or not os.path.exists(ctx.config_path):
        return
    # The config shipped beside the linter spells out every key on purpose — it is the
    # reference, and a project with no config of its own is linted against it.
    if os.path.samefile(ctx.config_path,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "lint_workbook.toml")):
        return
    defaults = dict(DEFAULTS["limits"])
    defaults.update(TIER_LIMITS[ctx.tier])
    where = os.path.relpath(ctx.config_path, ctx.root).replace("\\", "/")
    section, comment_above = None, False
    for line in read(ctx.config_path).splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            section, comment_above = stripped.strip("[] "), False
            continue
        if not stripped:
            comment_above = False
            continue
        if stripped.startswith("#"):
            comment_above = True
            continue
        if section == "limits" and "=" in stripped:
            key = stripped.split("=", 1)[0].strip().strip('"').strip("'")
            commented = comment_above or "#" in stripped.split("=", 1)[1]
            value = ctx.limits.get(key)
            if key in defaults and value == defaults[key]:
                warn(where, f"limits: {key} = {value!r} is the default — remove the line")
            elif key not in ("enforce",) and not commented:
                warn(where, f"limits: {key} overrides the default with no comment saying why")
        comment_above = False


def check_absolute_paths(ctx):
    """5. Absolute paths outside the repository, checked for existence.

    This is how a pointer to the standard rotted in one project: the path sat in prose
    rather than in a link, so a markdown-link check missed it, for months, in the file
    that governs all the others.
    """
    for path in linted_docs(ctx):
        text = strip_code(read(path))
        ticked = [m.group(1) for m in ABS_PATH_TICKED_RE.finditer(text)]
        bare = [m.group(0) for m in
                ABS_PATH_BARE_RE.finditer(ABS_PATH_TICKED_RE.sub("", text))]
        for target in ticked:
            target = target.rstrip(".,;: ")
            if any(c in target for c in PATH_PLACEHOLDER_CHARS):
                continue
            if not os.path.exists(target):
                err(ctx.rel(path), f"absolute path does not exist: {target}")
        for target in bare:
            target = target.rstrip(".,;: ")
            if os.path.exists(target) or any(c in target
                                             for c in PATH_PLACEHOLDER_CHARS):
                continue
            # A bare path stops at the first space, and a project root may contain one.
            # Reporting a correct path as an error is worse than asking for backticks,
            # so if the truncation point is a real directory, say so.
            if os.path.isdir(os.path.dirname(target)) and not os.path.isdir(target):
                warn(ctx.rel(path), f"absolute path may be truncated at a space: "
                                    f"{target} — write it in backticks so it can be "
                                    f"checked")
            else:
                err(ctx.rel(path), f"absolute path does not exist: {target}")


def check_rel_paths(ctx):
    """6. Repo-relative paths in backticks, checked for existence."""
    for path in linted_docs(ctx):
        doc_dir = os.path.dirname(path)
        for token in REL_PATH_RE.findall(strip_code(read(path))):
            if any(c in token for c in PATH_PLACEHOLDER_CHARS) \
                    or token.startswith("/") or token in ctx.path_allow:
                continue  # a placeholder, an absolute device path, or a declared absence
            if not resolve_rel_path(ctx, token, doc_dir):
                err(ctx.rel(path), f"path does not exist anywhere: {token}")


def check_journal_index(ctx):
    """7. The journal index against its own entries — it grows fastest of all."""
    path = os.path.join(ctx.docs, "journal.md")
    if not os.path.exists(path):
        return
    text = strip_code(read(path))
    # Counted, not set-compared: when several entries share a date, comparing sets makes
    # a missing index line for one of them invisible.
    entries = Counter(re.findall(r"^## (\d{4}-\d{2}-\d{2})\b", text, re.MULTILINE))
    indexed = Counter(re.findall(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*", text, re.MULTILINE))
    for date in sorted(set(entries) | set(indexed)):
        if entries[date] != indexed[date]:
            err(ctx.rel(path), f"{date}: {entries[date]} entr(ies) but "
                               f"{indexed[date]} index line(s)")


VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
POINTER_RE = re.compile(r"https?://\S+|`[^`\n]*[/\\][^`\n]*`|\]\([^)]+\)")


def check_meta(ctx):
    """18. _meta.md exists, names the standard, and records the version (H10).

    Promoted from a warning to an error on 2026-09-13, under the release policy in
    DEVIATIONS.md §6: a tightening change ships as a warning and becomes an error once
    every consumer is clean. All six were, so it is one.

    Without this file a document set cannot say which rules it is being held to, and a
    session has to infer them from the shape of what is already there — which reproduces
    whatever was already wrong. Without the *version* on the line, "has not caught up
    with the standard yet" and "was never kept to it" look identical, and the two call
    for very different responses.
    """
    path = os.path.join(ctx.docs, "_meta.md")
    if not os.path.exists(path):
        err(ctx.rel(path), "missing — nothing here says which standard these documents "
                           "are kept to, or which version of it")
        return
    text = strip_code(read(path))
    label = ctx.labels.get("standard", "Standard")
    line = next((ln for ln in text.splitlines() if ln.strip().startswith(label)), None)
    if line is None or not POINTER_RE.search(line):
        err(ctx.rel(path), f"no '{label}' line naming the standard — a URL, a path or a "
                           f"link to the rules these documents follow")
        return
    if not VERSION_RE.search(line):
        err(ctx.rel(path), "the standard is named but no version is recorded — without "
                           "one, 'has not caught up yet' and 'was never kept to it' "
                           "look the same")


CRITICAL_RULES_RE = re.compile(r"^(?:#+\s*)?\**critical rules\**:?\s*$", re.IGNORECASE)
ID_TOKEN_RE = re.compile(r"\b[A-Z]{1,3}\d+\b")
POINTER_RULES_WARN = 5
POINTER_LINES_WARN = 20


def pointer_rules(text):
    """Top-level bullets under a 'Critical rules' heading or label, continuations joined."""
    rules, inside = [], False
    for line in text.splitlines():
        if not inside:
            inside = bool(CRITICAL_RULES_RE.match(line.strip()))
            continue
        if line.startswith("#"):
            break
        if re.match(r"[-*]\s", line):
            rules.append(line)
        elif rules and line.strip():
            if not line[0].isspace():
                break
            rules[-1] += " " + line.strip()
    return rules


def check_root_pointers(ctx, known):
    """19. Every critical rule in a root pointer is also stated in project-workbook/ (H11).

    A pointer is the one file an agent's tool loads into every session, so it is where a
    session reaches when told "write this down so it does not happen again" — and a rule
    written only there is knowledge with no home in the documents, invisible to every
    other tool and to people. So each rule has to say where in the document set it lives:
    a path into the docs that exists, or a register id that resolves.

    A missing place is an error. Under the release policy in DEVIATIONS.md §6 it would
    ship as a warning; it was measured across every consumer first, the six rules it
    flagged were each already stated in their documents and only lacked the path, and
    with those added all were clean — so it ships as an error, as H10 became one.

    Too many rules or too many lines only warn: the admission test for a rule
    (METHODOLOGY §5) is a judgement, and a count cannot make it.
    """
    docs_rel = os.path.relpath(ctx.docs, ctx.root).replace("\\", "/") + "/"
    path_re = re.compile(re.escape(docs_rel) + r"[^\s`)\]#]*")
    for pointer in ctx.root_pointers:
        if not os.path.exists(pointer):
            continue
        text = strip_code(read(pointer))
        where = ctx.rel(pointer)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if len(lines) > POINTER_LINES_WARN:
            warn(where, f"{len(lines)} lines, over {POINTER_LINES_WARN} — a pointer that "
                        f"grows is turning into a second home for the docs; advisory")
        rules = pointer_rules(text)
        if len(rules) > POINTER_RULES_WARN:
            warn(where, f"{len(rules)} critical rules, over {POINTER_RULES_WARN} — check "
                        f"each against the admission test in METHODOLOGY §5; advisory")
        for rule in rules:
            paths = [p.rstrip(".,;:") for p in path_re.findall(rule)]
            stated = (any(os.path.exists(os.path.join(ctx.root, p)) for p in paths)
                      or any(t in known for t in ID_TOKEN_RE.findall(rule)))
            if not stated:
                head = re.sub(r"^[-*]\s+", "", rule).strip()[:60]
                err(where, f"critical rule not stated in {docs_rel} — give the path or "
                            f"the register id where it lives (H11): \"{head}…\"")


def check_onboarding(ctx):
    """21. The project has a file for the person joining it, and its links resolve.

    AGENTS.md and the workbook are for the agent. Nothing told a person who clones the
    project what works with nothing installed, which hooks and tools to set up, and
    which mods or skills to enable in their own agent — and a repository cannot enable a
    mod for a visitor, so that step is theirs to take or it does not happen.

    Warnings only, both of them: the file is new in v3.1, and under the release policy
    (DEVIATIONS.md §6) a check that tightens the standard ships as a warning.
    """
    if ctx.onboarding is None:
        return
    where = ctx.rel(ctx.onboarding)
    if not os.path.exists(ctx.onboarding):
        warn(where, "absent — what a person joining the project installs and enables; "
                    "see templates/ONBOARDING.md (RULES.md §1)")
        return
    for target in MD_LINK_RE.findall(strip_code(read(ctx.onboarding))):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(ctx.onboarding), target))
        if not os.path.exists(resolved):
            warn(where, f"broken link -> {target}")


def check_tier_inventory(ctx):
    """A file expected from this tier upward is absent (RULES.md §1, Tier column).

    A warning, and deliberately quiet below the tier: the point of the column is that a
    small project running on few files is complete, not half-documented.
    """
    reached = TIERS[:TIERS.index(ctx.tier) + 1]
    for tier in reached:
        for name in TIER_INVENTORY.get(tier, []):
            if not os.path.exists(os.path.join(ctx.docs, name)):
                warn(ctx.rel(os.path.join(ctx.docs, name)),
                     f"expected from tier {tier} upward and absent (this project is "
                     f"{ctx.tier}) — see the Tier column in RULES.md")


# --- research-profile checks --------------------------------------------------------

def check_backlog_statuses(ctx):
    """9. Every backlog status belongs to the legend the file declares."""
    if not os.path.exists(ctx.backlog):
        return
    text = strip_code(read(ctx.backlog))
    m = re.search(re.escape(ctx.legend_label) + r"\s*([^\n]+)", text)
    if not m:
        err(ctx.rel(ctx.backlog),
            f"no '{ctx.legend_label}' line — statuses cannot be validated")
        return
    # Prefer the backticked items. A legend names its statuses in backticks by house
    # style, and backticks are unambiguous where a separator is a guess: splitting on a
    # fixed set of punctuation read a legend joined by "·" as one long item, so every
    # status in the table was "not in the legend" — nine errors against a correct file,
    # which is how a check earns being ignored.
    raw = m.group(1)
    ticked = re.findall(r"`([^`]+)`", raw)
    items = ticked or re.split(r"[/,;|·•]", raw)
    legend = {clean_cell(s) for s in items if clean_cell(s)}
    col = status_column(text)
    for line in text.splitlines():
        row = ctx.task_re.match(line)
        if not row:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None or col >= len(cells):
            continue
        head = re.split(r"[\s(—-]", clean_cell(cells[col]), 1)[0].strip()
        if head and head not in legend:
            err(ctx.rel(ctx.backlog), f"{row.group(1)}: status '{head}' is not in the "
                                      f"legend ({', '.join(sorted(legend))})")


def clean_cell(s):
    """A table cell or legend item without markdown emphasis, backticks or padding.

    Stripped repeatedly rather than in a fixed order: `**Status legend:** `open`` leaves
    whitespace between the emphasis and the backtick, and a single pass gives up there.
    """
    prev = None
    while prev != s:
        prev = s
        s = s.strip().strip("*").strip("`")
    return s


def status_column(text):
    """Index of the status column, read from the table header.

    Positional assumptions do not survive contact with other people's tables — a
    backlog whose columns are id / status / task / phase would otherwise have its
    *phase* validated against the status legend. Falls back to the last column, which
    is the only sensible guess when no header names a status.
    """
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [clean_cell(c).lower() for c in line.strip().strip("|").split("|")]
        for i, c in enumerate(cells):
            if c in ("status", "state"):
                return i
        if any(cells):
            return len(cells) - 1  # first table row, no status header: guess the last
    return None


def check_done_tasks(ctx):
    """10. A backlog task marked done with no journal entry."""
    journal = os.path.join(ctx.docs, "journal.md")
    if not (os.path.exists(ctx.backlog) and os.path.exists(journal)):
        return
    # Anchored to journal headings, not to the id appearing anywhere in the file: a
    # passing mention inside some other entry is not a record of the work.
    headings = "\n".join(re.findall(r"^## .*$", read(journal), re.MULTILINE))
    for line in read(ctx.backlog).splitlines():
        m = ctx.task_re.match(line)
        if m and re.search(r"\|\s*done\b", line) and not re.search(
                rf"^## .*\b{re.escape(m.group(1))}\b", headings, re.MULTILINE):
            err(ctx.rel(ctx.backlog),
                f"{m.group(1)} is done but no journal.md entry is headed with it")


def check_reports(ctx, ids):
    """11. Required fields of every measurement report, and its id against the register."""
    if not ctx.baseline or not os.path.isdir(ctx.baseline):
        return
    field = ctx.cfg["measurement"]["id_field"]
    raw_dir = ctx.cfg["measurement"]["raw_dir"]
    for dirpath, _, names in os.walk(ctx.baseline):
        # raw/ holds the reports a baseline was curated from, kept so the result can be
        # re-derived. They are inputs, not stored measurements.
        if raw_dir and os.path.basename(dirpath) == raw_dir:
            continue
        for n in sorted(names):
            if not n.endswith(".json"):
                continue
            path = os.path.join(dirpath, n)
            try:
                data = json.loads(read(path))
            except json.JSONDecodeError as e:
                err(ctx.rel(path), f"invalid JSON: {e}")
                continue
            # null is a legitimate value (a baseline has no experiment); a missing key
            # is not.
            for required in ctx.cfg["measurement"]["required_fields"]:
                if required not in data:
                    err(ctx.rel(path), f"required field '{required}' is missing")
            cid = data.get(field)
            if cid is None:
                err(ctx.rel(path), f"{field} is null — a stored measurement must name "
                                   f"its configuration")
            elif cid not in ids:
                err(ctx.rel(path), f"{field} '{cid}' is not registered in corpus.md")
            elif os.path.basename(dirpath) != cid:
                err(ctx.rel(path), f"{field} '{cid}' does not match its directory")


def check_corpus_index(ctx, ids):
    """12. The corpus index against the configurations that parse as registered.

    Planned configurations are deliberately prose rather than `## <id>` headings: a
    heading would make the harness accept a configuration that has no data and no
    baseline. The index must therefore separate the two, and its Registered rows must
    match reality.
    """
    if not ctx.corpus or not os.path.exists(ctx.corpus):
        return
    text = strip_code(read(ctx.corpus))
    m = re.search(r"^##+\s*Registered\b(.*?)(?=^##+\s|\Z)", text,
                  re.DOTALL | re.MULTILINE)
    if m:
        scope = m.group(1)
    else:
        # A register with no planned configurations needs no split, and demanding the
        # heading anyway is ceremony. Fall back to the whole index: the mismatch check
        # below is what actually catches a planned configuration written as a heading.
        head = re.search(r"^##+\s*\S+.*?$(.*?)(?=^---|\Z)", text,
                         re.DOTALL | re.MULTILINE)
        scope = head.group(1) if head else text
        warn(ctx.rel(ctx.corpus),
             "index has no 'Registered' section — planned and registered configurations "
             "cannot be told apart; fine if nothing here is planned")
    listed = set(re.findall(r"[|-]\s*\*{0,2}`?([a-z0-9][a-z0-9-]*)`?\*{0,2}\s*[|·—-]",
                            scope))
    for missing in sorted(ids - listed):
        err(ctx.rel(ctx.corpus),
            f"'{missing}' has an entry but is not in the Registered index")
    for missing in sorted(listed - ids):
        err(ctx.rel(ctx.corpus),
            f"'{missing}' is listed as Registered but has no '## {missing}' entry")


def report_id(ctx, ref, doc_dir):
    """The configuration a referenced report actually belongs to."""
    field = ctx.cfg["measurement"]["id_field"]
    for root in ctx.path_roots + [doc_dir]:
        candidate = os.path.join(root, ref)
        if os.path.exists(candidate):
            try:
                with open(candidate, encoding="utf-8") as f:
                    return json.load(f).get(field)
            except (json.JSONDecodeError, OSError):
                return None
    return None


def check_numbers(ctx, ids):
    """13. Result numbers with no link to a source.

    Checked per line, not per paragraph: a paragraph-wide test lets one allow-phrase or
    one unrelated .json anywhere in a bullet list excuse every number in it. The link
    may wrap onto a neighbouring line, but no further.
    """
    paths = [os.path.join(ctx.docs, n) for n in ctx.cfg["numbers"]["result_files"]]
    if ctx.corpus:
        paths.append(ctx.corpus)
    for path in paths:
        if not os.path.exists(path):
            continue
        doc_dir = os.path.dirname(path)
        text = strip_code(read(path))
        # A prediction is exempt as a *block* — from "**Prediction.**" to the next bold
        # marker — not as a paragraph. Its bullets are often separated by a blank line,
        # and a paragraph-scoped exemption made the correct format fail, which taught
        # people to paste a fake .json reference.
        exempt = set()
        for m in ctx.prediction_block_re.finditer(text):
            exempt.update(range(m.start(), m.end()))
        lines = text.splitlines(keepends=True)
        offset = 0
        for i, line in enumerate(lines):
            here, offset = offset, offset + len(line)
            has_metric = bool(ctx.metric_re.search(line))
            numeric = ctx.number_re.search(line) or (has_metric
                                                     and BARE_NUMBER_RE.search(line))
            if not numeric or here in exempt:
                continue
            # An allow-phrase excuses prose, not a metric. "Beat the acceptance
            # criterion: 31.02 ms p50" used to pass on the strength of the phrase.
            if not has_metric and any(a in line for a in ctx.number_allow):
                continue
            window = "".join(lines[max(0, i - 1):i + 2])
            refs = [j for j in JSON_REF_RE.findall(window)
                    if resolve_rel_path(ctx, j, doc_dir)]
            if not refs:
                err(f"{ctx.rel(path)}:{i + 1}",
                    f"number with no link to an existing source: {line.strip()[:70]}")
                continue
            # Relevance, not just presence. The configuration a text is *about*, not the
            # one spelled inside the path it cites: a baseline filename contains its own
            # id, which would otherwise vouch for itself. The defect this exists for was
            # a figure about one configuration backed by another's baseline.
            prose = JSON_REF_RE.sub("", window)
            named = {c for c in ids if c in prose}
            for ref in refs:
                linked = report_id(ctx, ref, doc_dir)
                if named and linked and linked not in named:
                    err(f"{ctx.rel(path)}:{i + 1}",
                        f"number cites {os.path.basename(ref)} ('{linked}') while the "
                        f"text is about {', '.join(sorted(named))}")


def entry_bodies(text, prefix):
    """Yield (id, body) for every entry in a register, in file order."""
    marks = list(re.finditer(rf"^## ({prefix}\d+)\s*[.:]", text, re.MULTILINE))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        yield m.group(1), text[m.end():end]


def check_refuted_backlinks(ctx):
    """14. A refuted E## with no back-link from a plan file."""
    path = ctx.registers.get("E")
    if not path or not os.path.exists(path):
        return
    text = strip_code(read(path))
    plan_text = "".join(strip_code(read(p)) for p in md_files(ctx.plan_dir))
    for eid, body in entry_bodies(text, "E"):
        if ctx.status_refuted_re.search(body) and f"[[{eid}]]" not in plan_text:
            # What the back-link has to say is not fixed. "Refuted" can mean a dead end,
            # and then it reads "do not do this"; it can also mean refuted to the letter
            # of the prediction and adopted in substance, and then dictating that wording
            # would put a falsehood in the plan. What matters is that the task carries the
            # pointer, because an archive nobody opens at the moment of temptation is not
            # a defence.
            err(ctx.rel(path), f"{eid} is refuted and no plan file links to it — the task "
                               f"that tempted it needs a [[{eid}]] back-link carrying the "
                               f"lesson, see rule H9")


def check_predictions(ctx):
    """15. An E## that is not open, with an empty prediction."""
    path = ctx.registers.get("E")
    if not path or not os.path.exists(path):
        return
    text = strip_code(read(path))
    for eid, body in entry_bodies(text, "E"):
        if ctx.status_open_re.search(body):
            continue
        m = ctx.prediction_field_re.search(body)
        # Neither the lead-in line nor a generated threshold bullet proves anything:
        # both are written by the tool itself. A prediction is a statement naming a
        # quantity or a configuration — something a measurement can later contradict.
        body_lines = m.group(1).splitlines() if m else []
        raw_bullets = [l for l in body_lines if l.strip().startswith(("-", "*"))]
        if raw_bullets:
            candidates = [l for l in raw_bullets if not BOILERPLATE_BULLET_RE.search(l)]
        else:
            # A prediction written as prose rather than as a list is still a prediction.
            # Requiring bullets would fail a correct entry, and the lesson people take
            # from that is to satisfy the shape rather than to state a number.
            candidates = [l for l in body_lines if l.strip()]
        # A reconstructed prediction is held only to being present. The `retro` marker
        # already says its quality cannot be checked — nothing can verify it was not
        # fitted to the outcome — so demanding a figure of it buys a better-looking
        # reconstruction, not better evidence, and the way people satisfy that demand is
        # to add a number after the fact. A non-retro entry still has to name a quantity.
        retro = bool(ctx.status_retro_re.search(body))
        substantive = [l for l in candidates
                       if retro or re.search(r"\d", l) or f"[[{ctx.link_prefix}:" in l]
        if not substantive:
            if retro:
                err(ctx.rel(path), f"{eid} is marked retro but its Prediction block is "
                                   f"empty — a reconstruction still has to say what was "
                                   f"expected, see rule H7")
            else:
                err(ctx.rel(path), f"{eid} has a verdict but no actual prediction — the "
                                   f"Prediction block needs a bullet naming a quantity or "
                                   f"a configuration, see rule H7")


def check_acceptance_criteria(ctx):
    """16. An acceptance criterion that hedges instead of stating a number.

    A warning, not an error: a criterion can be legitimately qualitative ("the picture
    matches the reference"), but a hedge word with no figure beside it is the kind that
    cannot settle an argument later.
    """
    if not os.path.isdir(ctx.plan_dir):
        return
    for path in md_files(ctx.plan_dir):
        lines = read(path).splitlines()
        for i, line in enumerate(lines):
            marker = f"**{ctx.criterion_label}:**"
            if marker not in line:
                continue
            block = " ".join(lines[i:i + 3])
            # Metric names carry digits of their own (p99, ft_p50), so strip them before
            # asking whether the criterion states a figure.
            if HEDGE_RE.search(block) and not re.search(r"\d",
                                                        ctx.metric_re.sub("", block)):
                warn(f"{ctx.rel(path)}:{i + 1}",
                     "acceptance criterion hedges without a figure: "
                     + line.split(marker)[-1].strip()[:60])


# --- entry point --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Lint an project-workbook/ document set.")
    ap.add_argument("--config", default=os.path.join(os.path.dirname(__file__),
                                                     "lint_workbook.toml"))
    ap.add_argument("--root", help="project root (default: from config)")
    ap.add_argument("--docs", help="path to project-workbook/, relative to root")
    ap.add_argument("--profile", choices=["engineering", "research"])
    ap.add_argument("--tier", choices=list(TIERS),
                    help="size tier (default: from config, else S)")
    args = ap.parse_args()

    # If --docs is given as an absolute path, treat its parent as the root: the common
    # case is linting someone else's project without writing a config for it.
    root, docs = args.root, args.docs
    if docs and os.path.isabs(docs):
        root, docs = root or os.path.dirname(os.path.abspath(docs)), \
            os.path.basename(os.path.normpath(docs))

    cfg = load_config(args.config, [
        ("paths", "root", root),
        ("paths", "docs", docs),
        ("profile", "name", args.profile),
        ("project", "tier", args.tier),
    ])
    # A relative root in the config file is relative to that file, as the config
    # promises — not to wherever the linter happens to be run from. Resolved against
    # the working directory, a run from a subdirectory finds no docs, prints "nothing
    # to lint" and exits 0, which looks exactly like passing.
    if root is None and not os.path.isabs(cfg["paths"]["root"]) \
            and os.path.exists(args.config):
        cfg["paths"]["root"] = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(args.config)), cfg["paths"]["root"]))
    ctx = Ctx(cfg)

    # The docs are UTF-8 and quote their own content back in messages, but a Windows
    # console defaults to a legacy code page and raises UnicodeEncodeError on the first
    # em dash. A linter that dies while reporting is worse than no linter, so degrade
    # the output instead of the process.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if not os.path.isdir(ctx.docs):
        # An explicitly passed --docs that does not exist is a typo, and worth failing
        # on. A configured or default path that does not exist means there is simply no
        # document set here yet — which is the normal state of a project on its first
        # day, and of any repository that installed the pre-commit hook early. Failing
        # there teaches people to pass --no-verify, which disables the check for good.
        if args.docs:
            print(f"ERROR    no such directory: {ctx.docs}")
            sys.exit(1)
        print(f"nothing to lint: {ctx.rel(ctx.docs)} does not exist")
        sys.exit(0)

    ids = corpus_ids(ctx) if ctx.research else set()
    known = set()
    for prefix in ctx.registers:
        known |= register_ids(ctx, prefix)[0]
    known |= task_ids(ctx) | delta_ids(ctx)
    known |= {f"{ctx.link_prefix}:{c}" for c in ids}

    check_links(ctx, known)
    check_registers(ctx)
    check_register_size(ctx)
    check_line_limits(ctx)
    check_limit_overrides(ctx)
    check_absolute_paths(ctx)
    check_rel_paths(ctx)
    check_journal_index(ctx)
    check_meta(ctx)
    check_root_pointers(ctx, known)
    check_onboarding(ctx)
    check_tier_inventory(ctx)
    if ctx.research:
        check_backlog_statuses(ctx)
        check_done_tasks(ctx)
        check_reports(ctx, ids)
        check_corpus_index(ctx, ids)
        check_numbers(ctx, ids)
        check_refuted_backlinks(ctx)
        check_predictions(ctx)
        check_acceptance_criteria(ctx)

    for w in warnings:
        print(f"warning  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) "
          f"[{cfg['profile']['name']} profile, tier {ctx.tier}]")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
