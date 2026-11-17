# Contributing

The architecture catalog is the extension point. Edit `catalog/architectures.yaml`, then run `python3 tools/generate_catalog.py`; do not hand-edit generated README tables or indexes.

- New architecture: copy an existing `architectures/*/architecture.md` and keep its sections (workload, data flow, B2 zones, boundaries, capability map, integration configuration, security, references). Name it by workflow, not tool. Add its audience, problem, workflow, capabilities, scale, security, compliance and links to the catalog. Reuse `examples/` configs instead of duplicating them.
- New integration: add it under the relevant catalog architecture with its role, connection method, `connection_type`, authoritative documentation `url` and, where one exists, a `setup_url` for the B2 setup guide. Connection types and their labels are shared across the B2 category repos (see `CONNECTION_LABELS` in `tools/generate_catalog.py`). "Supports S3" is not enough: link docs or source that show a configurable endpoint, a B2 option, or a generic S3-compatible option. If a tool serves several architectures, define it once and reuse it with a YAML alias. Add a new `connection_type` only with a schema, generator label and test update.
- New sample application: build it in its own repository (for example under `backblaze-b2-samples`) and add a `samples:` entry with `group`, `summary`, `description` and, where it fits, `architectures` and `relevance`. The generator renders the README, `docs/related-b2-samples.md`, `llms.txt` and skill tables.
- Regenerate `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt` and `llms-full.txt` in the same change, and update `docs/robotics.md` when the category story changes.

Content rules: attribute to a vendor only what its docs or code show; label B2-side patterns as such; never hardcode a region or endpoint; link B2 pricing instead of quoting numbers.
Security: no real keys anywhere; secrets in gitignored `0600` `.env`; scoped keys, not master, unless provisioning requires it (say so).
Tests: `python3 tools/generate_catalog.py --check`, `python3 tools/check_markdown_links.py`, `python3 -m pytest tests`. Run `python3 tools/check_markdown_links.py --external` when adding outbound links.
