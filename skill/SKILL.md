---
name: b2-robotics
description: Design or review Backblaze B2 storage for robotics, including rosbag2/MCAP log offload, Foxglove or Rerun replay, DuckDB session search, LeRobot or Zarr teleop datasets, MuJoCo or Isaac Sim rollouts, Ray Train checkpoints, MLflow/W&B/ClearML tracking, policy releases to the fleet, and KISS-ICP or Open3D mapping archives. Use for bucket and prefix layout, key scoping, presigned URLs, CORS, Object Lock, lifecycle, or deciding what stays off object storage.
---

# B2 for robotics

Choose a workflow from the bundled [architecture catalog](references/architecture-catalog.md), which also lists related B2 sample applications.

For changing service behavior, limits, and setup steps, use the canonical [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage). Link pricing claims to [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) instead of copying numbers.

## Rules
- Use the S3-compatible API. Derive `https://s3.<region>.backblazeb2.com` from `B2_REGION`; never hardcode region or endpoint.
- Env: `B2_APPLICATION_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`, `B2_REGION`, optional `B2_ENDPOINT`. Secrets in gitignored 0600 `.env`; never print keys.
- A key scopes to one bucket + one prefix + capabilities. Roles: offload-signer, catalog-writer, replay-signer, evidence-writer, trainer-reader, trainer-checkpoints, release-publisher, release-signer (mints presigned GETs for robots and CI). Cross-bucket promotion needs a short-lived key covering both buckets. Master key only for provisioning.
- Robots and browsers get presigned URLs, never keys. A single presigned PUT or CopyObject is limited to 5 GB; use presigned upload-part URLs and UploadPartCopy above that.
- Bucket names are globally unique; prefix with the org and expect collisions.
- Upload only closed files. Retain the local copy until the offload service verifies the exact uploaded version's size and full-file SHA-256 and returns a verification receipt.
- Evidence and policy releases go in dedicated Object Lock buckets (governance by default). Lifecycle does not delete locked versions.
- Lifecycle uses B2 semantics (hide, then delete by age and prefix). It cannot keep "the last K"; use the trainer (Ray `num_to_keep`).
- Event Notifications must be enabled by Backblaze Support; webhooks are signed and at-least-once, so be idempotent.
- Cloud Replication is bucket-to-bucket DR, not fleet delivery. Enable Object Lock on both buckets before creating a replication rule.
- Configure each integration through its documented B2 backend, custom S3 endpoint, presigned URLs, or SDK-based worker. State the required operations and credential scope.
- rosbag2: record bounded MCAP splits locally; an offload agent presigned-PUTs closed splits (Rosbag2 Cloud Offload sample) and depots use `rclone copy` from closed-file staging directories. Local cleanup follows checksum verification.
- Foxglove app: presigned GET, range requests, no redirects, CORS for app.foxglove.dev and embed.foxglove.dev exposing ETag, Content-Type, Accept-Ranges, Content-Length. Foxglove Primary Site: `s3_compatible` with the B2 endpoint, plus a B2 Event Notification adapter that POSTs object-created events to `/site-bucket-notifications`.
- Rerun: pass a presigned GET for the `.rrd` to the Web Viewer, with CORS for its origin.
- LeRobot: sync finalized v3 dataset directories with rclone or s5cmd, or stream ranged GETs with the LeRobot B2 Streaming sample. KISS-ICP, Open3D and MuJoCo Playground write local files: sync them with rclone or s5cmd.
- Built-in B2 options: MLflow `b2://` and rclone's B2 backend. Ray Train, W&B, ClearML, Daft, DVC, and DuckDB use a custom S3 endpoint; Zarr uses s3fs `endpoint_url`.
- Isaac Sim: set the B2 endpoint, bucket and region in an `asset_region_profiles` entry to load USD assets.
- Overdrive only for sustained high-throughput reads; otherwise Standard B2 plus a local NVMe cache for repeated reads.

## Keep off B2
The live ROS graph and robot state, partially written bags and HDF5, upload queues, tracking-server and search databases, metrics, simulator and GPU state, Ray object store, and live USD editing.

## Verify

When operating inside the full repository, use its `AGENTS.md` validation commands. When this skill is installed by itself, use the linked product and integration documentation for configuration and service behavior.
