"""Rule engine: 'context' rules remember values, 'record' rules emit rows."""
import json
import re


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class Parser:
    """Config format:

    {
      "context": [{"name": "sample", "pattern": "^Sample ID:\\s*(?P<sample>\\S+)"}],
      "record":  [{"name": "reading", "pattern": "(?P<time>\\d\\d:\\d\\d:\\d\\d)\\s+(?P<value>[-\\d.]+)"}],
      "numeric": ["value"],
      "decimal_comma": false,
      "reset_on": "^End of run",
      "skip": ["^#", "^\\s*$"]
    }

    Each line is tested against skip, reset, context and record patterns. Named groups from context
    rules persist until overwritten (or reset); each record match emits one row = context + groups.
    """

    def __init__(self, config):
        self.config = config
        flags = re.IGNORECASE if config.get("ignore_case") else 0
        self.skip = [re.compile(p, flags) for p in config.get("skip", [])]
        self.reset = re.compile(config["reset_on"], flags) if config.get("reset_on") else None
        self.context_rules = [(r.get("name", "context"), re.compile(r["pattern"], flags)) for r in config.get("context", [])]
        self.record_rules = [(r.get("name", "record"), re.compile(r["pattern"], flags), r.get("findall", False))
                             for r in config.get("record", [])]
        if not self.record_rules:
            raise ValueError("config needs at least one 'record' rule")
        self.numeric = set(config.get("numeric", []))
        self.decimal_comma = config.get("decimal_comma", False)

    def _cast(self, k, v):
        if v is None:
            return ""
        v = v.strip()
        if k in self.numeric:
            t = v.replace(",", ".") if self.decimal_comma else v
            try:
                float(t)
                return t
            except ValueError:
                raise ValueError("field %r: %r is not numeric" % (k, v))
        return v

    def parse_lines(self, lines, source=""):
        """Yield (row_dict, warning) tuples; exactly one of them is not None."""
        ctx = {}
        for no, line in enumerate(lines, 1):
            line = line.rstrip("\r\n")
            if any(s.search(line) for s in self.skip):
                continue
            if self.reset and self.reset.search(line):
                ctx = {}
                continue
            for _, rx in self.context_rules:
                m = rx.search(line)
                if m:
                    ctx.update({k: v.strip() for k, v in m.groupdict().items() if v is not None})
            for name, rx, findall in self.record_rules:
                matches = list(rx.finditer(line)) if findall else ([rx.search(line)] if rx.search(line) else [])
                for m in matches:
                    row = dict(ctx)
                    try:
                        row.update({k: self._cast(k, v) for k, v in m.groupdict().items()})
                    except ValueError as exc:
                        yield None, "%s:%d: %s" % (source, no, exc)
                        continue
                    row["_rule"] = name
                    row["_line"] = no
                    if source:
                        row["_source"] = source
                    yield row, None

    def parse_text(self, text, source=""):
        rows, warnings = [], []
        for r, w in self.parse_lines(text.splitlines(), source):
            (rows if r is not None else warnings).append(r if r is not None else w)
        return rows, warnings


def columns_of(rows, meta=True):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols and (meta or not k.startswith("_")):
                cols.append(k)
    data = [c for c in cols if not c.startswith("_")]
    return data + [c for c in cols if c.startswith("_")]
