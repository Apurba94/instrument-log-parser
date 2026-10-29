# instrument-log-parser

**Turn messy instrument exports and log files (plate readers, sensors, chromatographs,
loggers) into tidy CSV with a small JSON file of regular-expression rules, no coding needed.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Instruments write vendor-specific text: header blocks with sample IDs and settings, followed by
readings, sometimes with decimal commas and error codes. Researchers copy-paste these into
spreadsheets by hand, which is slow and unreproducible. Declaring the format once lets every future
file be converted identically, and the rules document the format for others.

## How it works

- **context** rules capture values that apply to following lines (sample ID, wavelength, run date)
- **record** rules emit one row per match, combined with the current context
- `reset_on` clears context at run boundaries; `skip` ignores comments and blank lines
- `numeric` fields are validated (and decimal commas converted); bad values become warnings with file:line
- `findall` extracts several records from one line (e.g. `a=1 b=2`)
- Output adds `_rule`, `_line`, `_source` provenance columns (`--no-meta` to drop)

## Usage

```bash
pip install .
instrument-log-parser examples/plate_reader.json "raw/*.log" -o tidy.csv
```

See `examples/plate_reader.json` and `examples/run1.log` for a complete configuration.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
