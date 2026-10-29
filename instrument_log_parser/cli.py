"""Command-line interface for instrument-log-parser."""
import argparse
import csv
import glob
import os
import sys

from .core import Parser, columns_of, load_config


def main(argv=None):
    ap = argparse.ArgumentParser(prog="instrument-log-parser", description="Convert instrument logs to tidy CSV.")
    ap.add_argument("config", help="JSON rules file")
    ap.add_argument("logs", nargs="+", help="log files or glob patterns")
    ap.add_argument("-o", "--output", help="CSV output (default stdout)")
    ap.add_argument("--no-meta", action="store_true", help="omit _rule/_line/_source columns")
    ap.add_argument("--encoding", default="utf-8")
    args = ap.parse_args(argv)
    parser = Parser(load_config(args.config))
    paths = [p for pat in args.logs for p in (sorted(glob.glob(pat)) or [pat])]
    rows, warnings = [], []
    for p in paths:
        with open(p, encoding=args.encoding, errors="replace") as fh:
            r, w = parser.parse_text(fh.read(), os.path.basename(p))
        rows += r
        warnings += w
    cols = columns_of(rows, meta=not args.no_meta)
    fh = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    if args.output:
        fh.close()
    for msg in warnings[:20]:
        print("warning: " + msg, file=sys.stderr)
    print("%d file(s), %d row(s), %d warning(s)" % (len(paths), len(rows), len(warnings)), file=sys.stderr)
    return 1 if warnings else 0
