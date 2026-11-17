# Agent guide

Use this repository to design or review storage workflows for robotics teams using Backblaze B2.

<!-- CODEGRAPH_START -->
## CodeGraph

When a `.codegraph/` directory exists at the repository root, use `codegraph explore "<question or symbols>"` before grep, find, or broad file reads when locating or understanding code. If the directory does not exist, skip CodeGraph; indexing is a maintainer decision.
<!-- CODEGRAPH_END -->

## Sources of truth

1. `catalog/architectures.yaml` is the machine-readable catalog of architectures, third-party integrations (with `connection_type`) and external sample applications. `schemas/architecture-catalog.schema.json` validates it.
2. `architectures/*/architecture.md` contains the detailed design, B2 zones and security boundaries.
3. `examples/` contains B2 configuration templates and scoped-key commands.
4. Current Backblaze product behavior is authoritative at <https://www.backblaze.com/docs/cloud-storage>. Pricing is authoritative at <https://www.backblaze.com/cloud-storage/pricing>.

Describe the documented connection for each integration: a B2 backend or provider preset, a custom S3 endpoint, presigned URLs, or an application worker using an SDK. Specify the endpoint, region, addressing style, required operations, and credential scope. Attribute product capabilities to the linked vendor documentation or source code. Describe sample applications by the workflow they implement. Use `native-b2-option` for an actual B2 backend or B2-specific provider preset; use `s3-custom-endpoint` for a configurable S3 connection.

For a single-file read of the summary and every architecture, use `llms-full.txt`.

## Generated files

Run `python3 tools/generate_catalog.py` after editing the catalog. Do not hand-edit generated sections in `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt`, or `llms-full.txt`. `llms-full.txt` concatenates narrative pages, so regenerate after editing `docs/robotics.md` or any `architecture.md`.

Validate with:

```bash
python3 tools/generate_catalog.py --check
python3 tools/check_markdown_links.py            # add --external to probe outbound links
python3 -m pytest tests
```

## Operational invariants

- Derive `https://s3.<region>.backblazeb2.com` from the bucket region; do not hardcode a real region.
- Pick each integration's `connection_type` by how practitioners connect it: a B2 backend or B2-specific provider preset, S3 custom endpoint, fsspec/s3fs, presigned URLs, or an S3 sync tool (rclone, s5cmd) for tools that write local files.
- Use scoped application keys (one bucket, one prefix, listed capabilities). Robots and browsers get presigned URLs, not keys. Keep master or administrative keys out of runtime services.
- Treat presigned URLs as bearer credentials.
- Upload only closed files (bag splits, HDF5, episodes); never overwrite a released dataset or policy version.
- Keep the ROS graph, robot state, queues, tracking and search databases, simulator state and compute off object storage.
- Never commit credentials, real presigned URLs, or robot data.
