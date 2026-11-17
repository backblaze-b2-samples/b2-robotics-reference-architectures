# B2 reference architectures for robotics

How robotics teams use Backblaze B2 across robot log offload, fleet search and replay, teleoperation datasets, simulation rollouts, policy training and release, and LiDAR mapping archives. Each architecture documents the data flow, B2 zones and security boundaries, and links out to the third-party integrations and B2 sample applications that implement it.

Learn more about [Backblaze B2 for AI and machine learning](https://www.backblaze.com/cloud-storage/industries/ai-ml).

Start with the [architecture index](docs/architecture-index.md) or the [agent-readable summary](docs/robotics.md). Current B2 product behavior is documented at [backblaze.com/docs](https://www.backblaze.com/docs/cloud-storage).

## Where does Backblaze B2 fit for robotics?

Most robotics data is written once and read many times by replay tools, dataloaders and trainers. B2 is the S3-compatible system of record behind that work.

- **Store in B2:** rosbag2/MCAP log lakes and session catalogs, teleop datasets, simulation rollouts, checkpoints, eval artifacts, LiDAR scans and maps.
- **Read from B2:** range GETs for replay and streaming training, presigned GETs for browser viewers, robots and CI, query in place with DuckDB.
- **Protect in B2:** Object Lock on incident evidence and released policies, versions, lifecycle (hide, then delete).
- **Connect tools:** use MLflow's `b2://` artifact backend or rclone's B2 backend; configure Ray Train, W&B, and ClearML with the regional S3 endpoint. Use presigned URLs for HTTP consumers and rclone or s5cmd to transfer closed files from rosbag2, LeRobot, KISS-ICP, and Open3D workers.
- **Keep elsewhere:** the live ROS graph and robot state, partially written files, upload queues, tracking and search databases, simulator and GPU state.

Pricing, egress terms and limits change: see [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) and the [B2 docs](https://www.backblaze.com/docs/cloud-storage).

## Architectures

<!-- catalog:architectures:start -->
| Architecture | Purpose | Samples and setup |
|---|---|---|
| [Offload robot logs from the fleet into a raw log lake](architectures/robot-log-offload/architecture.md) | Robots record split rosbag2/MCAP files locally; an offload agent uploads each closed split to B2 over intermittent links, deletes the local copy only after the stored version's size and SHA-256 match the closed split, catalogs each session in Parquet, and copies incident windows into a separate Object Lock evidence bucket. | [Rosbag2 Cloud Offload](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload) · [Roboflow Inference Frame Archive](https://github.com/backblaze-b2-samples/roboflow-inference-frame-archive) · [B2 Event Broker](https://github.com/backblaze-b2-samples/b2-event-broker) |
| [Search, visualize and replay fleet sessions from the log lake](architectures/fleet-search-replay/architecture.md) | Engineers query the session catalog in place to find sessions by robot, date, topic, or event, then open the matching MCAP or RRD files in browser viewers over presigned range reads, or download splits by presigned GET and replay them locally with ros2 bag play. | [Rosbag2 Cloud Offload](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload) · [DuckDB Query In Place](https://github.com/backblaze-b2-samples/duckdb-query-in-place) · [setup](https://docs.foxglove.dev/docs/primary-sites/installation) |
| [Record teleoperation demonstrations and stream imitation-learning datasets](architectures/teleop-imitation-datasets/architecture.md) | Teleop episodes are written in the LeRobot v3 layout or as Zarr replay buffers under versioned dataset prefixes on B2, curated in place, frozen as immutable versions, and streamed to trainers with ranged GETs instead of full downloads. | [LeRobot B2 Streaming](https://github.com/backblaze-b2-samples/lerobot-b2-streaming) |
| [Generate simulation rollouts and synthetic demonstrations at scale](architectures/sim-rollout-datasets/architecture.md) | Parallel simulation workers load shared USD and MJCF assets from B2 and write each completed episode (video, state/action/reward arrays, summary JSON) to an append-only run prefix used for behavioral cloning, offline RL, and evaluation baselines. | [MuJoCo Rollout Dataset](https://github.com/backblaze-b2-samples/mujoco-rollout-dataset) · [Mountpoint for S3 CSI driver with B2](https://github.com/backblaze-b2-samples/b2-integration-mountpoint-csi) |
| [Train and evaluate robot policies, checkpoint runs, and release models to the fleet](architectures/policy-training-registry/architecture.md) | Distributed visuomotor and VLA policy training streams data from B2 and writes checkpoints for fault-tolerant resume; runs and eval artifacts are tracked with lineage to dataset versions, and promoted policies are copied to a locked release prefix that robots and CI pull by presigned GET. | [WebDataset Streaming PyTorch Training](https://github.com/backblaze-b2-samples/webdataset-streaming-pytorch-training) · [Ray Train/Tune checkpoints notebook](https://github.com/backblaze-b2-samples/notebooks/tree/main/ray-train-tune-checkpoints) · [HF Cache Sync](https://github.com/backblaze-labs/hf-cache-sync) · [Mountpoint for S3 CSI driver with B2](https://github.com/backblaze-b2-samples/b2-integration-mountpoint-csi) · [setup](https://docs.ray.io/en/latest/train/user-guides/persistent-storage.html) |
| [Archive LiDAR mapping sessions and publish site maps to robots](architectures/mapping-session-archive/architecture.md) | LiDAR scans from mobile robots are archived per session; odometry and point-cloud jobs write poses, map snapshots, and trajectories beside the raw scans, and approved site maps are promoted to versioned prefixes that robots and RViz pull by presigned GET. | [KISS-ICP LiDAR Archive](https://github.com/backblaze-b2-samples/kiss-icp-lidar-archive) · [Open3D Point Cloud Pipeline](https://github.com/backblaze-b2-samples/open3d-point-cloud-pipeline) |
<!-- catalog:architectures:end -->

## Third-party integrations

Connection types: **S3 custom endpoint** (the tool documents a configurable endpoint or generic S3-compatible option), **Built-in Backblaze B2 option** (a B2 backend or B2-specific provider preset), **fsspec / s3fs** (reached through s3fs `endpoint_url`), **Presigned URLs** (the tool opens a short-lived presigned URL and never holds a B2 key), and **S3 sync tool** (rclone, s5cmd, or an offload agent transfers closed files between local storage and B2).

<!-- catalog:integrations:start -->
| Tool | Role | Connection type | How it connects to B2 | Architectures |
|---|---|---|---|---|
| [ROS 2 rosbag2](https://github.com/ros2/rosbag2) | On-robot recording of ROS 2 topics into split MCAP or SQLite bag files | S3 sync tool | Record bounded MCAP splits locally (`ros2 bag record -s mcap -d <seconds>`); an offload agent presigned-PUTs each closed split to `bags/<robot>/<session>/` and HEAD-confirms it before deleting the local copy (Rosbag2 Cloud Offload sample), and depots move bulk sessions with `rclone move` to the same prefix ([setup guide](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload/blob/main/ARCHITECTURE.md)) | [Offload robot logs from the fleet into a raw log lake](architectures/robot-log-offload/architecture.md) |
| [rclone](https://rclone.org/b2/) | Bulk sync of closed log, HDF5, or rollout directories from depots, docks, and sim farms | Built-in Backblaze B2 option | Native B2 backend with chunked large-file upload (--b2-chunk-size, --b2-upload-concurrency) | [Offload robot logs from the fleet into a raw log lake](architectures/robot-log-offload/architecture.md), [Generate simulation rollouts and synthetic demonstrations at scale](architectures/sim-rollout-datasets/architecture.md) |
| [DuckDB (httpfs)](https://duckdb.org/docs/current/core_extensions/httpfs/s3api.html) | SQL over the session catalog Parquet in place | S3 custom endpoint | `CREATE SECRET (TYPE s3, ENDPOINT 's3.<region>.backblazeb2.com', REGION '<region>')`, then query `s3://` paths | [Search, visualize and replay fleet sessions from the log lake](architectures/fleet-search-replay/architecture.md) |
| [Foxglove app (remote files)](https://docs.foxglove.dev/docs/visualization/connecting/cloud-data) | Browser visualization of MCAP sessions | Presigned URLs | Opens a presigned GET URL to the B2 object directly (no redirects); requires range requests and bucket CORS for the Foxglove origins | [Search, visualize and replay fleet sessions from the log lake](architectures/fleet-search-replay/architecture.md) |
| [Foxglove Primary Site (self-managed)](https://docs.foxglove.dev/docs/primary-sites/installation) | Self-hosted ingestion and indexing of recordings for streaming to the Foxglove app | S3 custom endpoint | Set Helm storageProvider s3_compatible and S3_COMPATIBLE_SERVICE_URL to `https://s3.<region>.backblazeb2.com` for the inbox and lake buckets; configure a B2 Event Notification rule on the inbox and a small adapter that verifies the B2 webhook signature and POSTs to the Primary Site bucket-notifications endpoint ([setup guide](https://docs.foxglove.dev/docs/primary-sites/configure-cloud-credentials)) | [Search, visualize and replay fleet sessions from the log lake](architectures/fleet-search-replay/architecture.md) |
| [Rerun Web Viewer](https://rerun.io/docs) | Browser playback of archived .rrd recordings | Presigned URLs | Pass a presigned GET URL for the .rrd to WebViewer.start(), and add the viewer origin to the bucket CORS rules ([setup guide](https://ref.rerun.io/docs/js/0.37.0/web-viewer/classes/WebViewer.html)) | [Search, visualize and replay fleet sessions from the log lake](architectures/fleet-search-replay/architecture.md) |
| [Hugging Face LeRobot](https://github.com/huggingface/lerobot) | Robot-learning dataset format (v3), recording, and training framework | S3 sync tool | LeRobot records and loads v3 datasets from a local root; sync the finalized dataset directory to `datasets/<name>/<version>/` with rclone or s5cmd and back to each trainer's local root, or stream ranged GETs straight from B2 with the LeRobot B2 Streaming sample ([setup guide](https://github.com/backblaze-b2-samples/lerobot-b2-streaming/blob/main/ARCHITECTURE.md)) | [Record teleoperation demonstrations and stream imitation-learning datasets](architectures/teleop-imitation-datasets/architecture.md) |
| [Daft (LeRobot reader)](https://docs.daft.ai/en/stable/datasets/lerobot/) | Lazy dataframe reads of LeRobot datasets for curation and relabeling | S3 custom endpoint | `daft.datasets.lerobot.read('s3://...', io_config=IOConfig(s3=S3Config(endpoint_url='https://s3.<region>.backblazeb2.com')))` ([setup guide](https://docs.daft.ai/en/stable/api/config/)) | [Record teleoperation demonstrations and stream imitation-learning datasets](architectures/teleop-imitation-datasets/architecture.md) |
| [Zarr (via s3fs)](https://zarr.dev/) | Chunked replay buffers for diffusion-policy and UMI-style training | fsspec / s3fs | FsspecStore over `s3fs.S3FileSystem(endpoint_url='https://s3.<region>.backblazeb2.com')` ([setup guide](https://s3fs.readthedocs.io/en/latest/)) | [Record teleoperation demonstrations and stream imitation-learning datasets](architectures/teleop-imitation-datasets/architecture.md) |
| [DVC](https://dvc.org/) | Dataset version pointers in git; the DVC remote stores its own content-addressed copy under `dvc/` | S3 custom endpoint | `dvc remote modify <name> endpointurl https://s3.<region>.backblazeb2.com` ([setup guide](https://doc.dvc.org/user-guide/data-management/remote-storage/amazon-s3)) | [Record teleoperation demonstrations and stream imitation-learning datasets](architectures/teleop-imitation-datasets/architecture.md) |
| [MuJoCo Playground](https://playground.mujoco.org/) | GPU-accelerated MuJoCo environments and policy rollouts | S3 sync tool | Write each finished episode (MP4, .npy state/action/reward arrays, summary JSON) to a local run directory, then sync closed episodes to `rollouts/<env>/<policy>/<run_id>/` with rclone or s5cmd; the MuJoCo Rollout Dataset sample writes the same layout directly with boto3 ([setup guide](https://github.com/backblaze-b2-samples/mujoco-rollout-dataset/blob/main/ARCHITECTURE.md)) | [Generate simulation rollouts and synthetic demonstrations at scale](architectures/sim-rollout-datasets/architecture.md) |
| [NVIDIA Isaac Sim (asset region profiles)](https://developer.nvidia.com/isaac/sim) | Loading USD simulation assets from S3-compatible storage | S3 custom endpoint | Define an isaacsim.storage.native asset_region_profiles entry with endpoint `https://s3.<region>.backblazeb2.com`, bucket, and region, and select it with ISAACSIM_ASSET_REGION_PROFILE ([setup guide](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/py/source/extensions/isaacsim.storage.native/docs/SETTINGS.html)) | [Generate simulation rollouts and synthetic demonstrations at scale](architectures/sim-rollout-datasets/architecture.md) |
| [Ray Train](https://docs.ray.io/en/latest/train/user-guides/persistent-storage.html) | Distributed training with checkpoint persistence and resume | S3 custom endpoint | Configure Ray checkpoint storage: `storage_path='s3://<bucket>/<path>?endpoint_override=https://s3.<region>.backblazeb2.com'`, or set `AWS_ENDPOINT_URL_S3` and use a plain `s3://` path ([setup guide](https://docs.ray.io/en/latest/train/user-guides/persistent-storage.html#s3-compatible-storage-backblaze-b2-minio-etc)) | [Train and evaluate robot policies, checkpoint runs, and release models to the fleet](architectures/policy-training-registry/architecture.md) |
| [MLflow](https://mlflow.org/) | Experiment tracking and model registry artifact store | Built-in Backblaze B2 option | Native `b2://<bucket>@s3.<region>.backblazeb2.com/<path>` artifact URI ([setup guide](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/#backblaze-b2)) | [Train and evaluate robot policies, checkpoint runs, and release models to the fleet](architectures/policy-training-registry/architecture.md) |
| [Weights & Biases (reference artifacts)](https://wandb.ai/) | Lineage tracking of datasets and checkpoints stored in B2 | S3 custom endpoint | Set `AWS_S3_ENDPOINT_URL=https://s3.<region>.backblazeb2.com` and log `s3://` references ([setup guide](https://docs.coreweave.com/guides/artifacts/track-external-files)) | [Train and evaluate robot policies, checkpoint runs, and release models to the fleet](architectures/policy-training-registry/architecture.md) |
| [ClearML](https://clear.ml/) | Experiment tracking, artifact storage, and pipeline orchestration | S3 custom endpoint | Add an sdk.aws.s3.credentials entry with `host: 's3.<region>.backblazeb2.com:443'` and `secure: true` (the port is required) ([setup guide](https://clear.ml/docs/latest/docs/integrations/storage/)) | [Train and evaluate robot policies, checkpoint runs, and release models to the fleet](architectures/policy-training-registry/architecture.md) |
| [KISS-ICP](https://github.com/PRBonn/kiss-icp) | LiDAR odometry and mapping | S3 sync tool | kiss_icp_pipeline writes poses (.npy, KITTI, TUM), config, and logs to a local results directory; sync each session's results to `trajectories/<session_id>/` with rclone or s5cmd; the KISS-ICP LiDAR Archive sample does the same with boto3 and presigned URLs ([setup guide](https://github.com/backblaze-b2-samples/kiss-icp-lidar-archive/blob/main/ARCHITECTURE.md)) | [Archive LiDAR mapping sessions and publish site maps to robots](architectures/mapping-session-archive/architecture.md) |
| [Open3D](https://www.open3d.org/) | Point-cloud downsampling, registration, meshing, and rendering | S3 sync tool | Open3D reads and writes PLY and PCD on local paths (`o3d.io.read_point_cloud`, `write_point_cloud`); copy scans down and sync job outputs to `jobs/<id>/` with rclone or s5cmd; the Open3D Point Cloud Pipeline sample does the same with the S3 API ([setup guide](https://github.com/backblaze-b2-samples/open3d-point-cloud-pipeline/blob/main/ARCHITECTURE.md)) | [Archive LiDAR mapping sessions and publish site maps to robots](architectures/mapping-session-archive/architecture.md) |
<!-- catalog:integrations:end -->

## Sample applications

Sample applications from [`backblaze-b2-samples`](https://github.com/backblaze-b2-samples) demonstrating these storage workflows. Follow the linked repositories for source code, setup, and operating instructions.

<!-- catalog:samples:start -->
| Sample | Demonstrates | Related architectures |
|---|---|---|
| [Rosbag2 Cloud Offload](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload) | Presigned-PUT offload of closed rosbag2 splits, HEAD-confirmed local deletes, a Parquet session catalog, and ros2 bag play replay from presigned GETs | [robot-log-offload](architectures/robot-log-offload/architecture.md), [fleet-search-replay](architectures/fleet-search-replay/architecture.md) |
| [LeRobot B2 Streaming](https://github.com/backblaze-b2-samples/lerobot-b2-streaming) | LeRobot v3 teleop datasets on B2 streamed to training workers with ranged GETs planned from the meta/episodes index | [teleop-imitation-datasets](architectures/teleop-imitation-datasets/architecture.md) |
| [MuJoCo Rollout Dataset](https://github.com/backblaze-b2-samples/mujoco-rollout-dataset) | MuJoCo Playground rollouts written to B2 as per-episode MP4, state/action/reward arrays, and summary JSON | [sim-rollout-datasets](architectures/sim-rollout-datasets/architecture.md) |
| [KISS-ICP LiDAR Archive](https://github.com/backblaze-b2-samples/kiss-icp-lidar-archive) | KISS-ICP odometry over LiDAR scans with scans, poses, .ply maps, and trajectories archived per session on B2 | [mapping-session-archive](architectures/mapping-session-archive/architecture.md) |
| [Open3D Point Cloud Pipeline](https://github.com/backblaze-b2-samples/open3d-point-cloud-pipeline) | Downsampling, registration, meshing, and rendering of point clouds stored on B2, with JSON job manifests | [mapping-session-archive](architectures/mapping-session-archive/architecture.md) |
| [Roboflow Inference Frame Archive](https://github.com/backblaze-b2-samples/roboflow-inference-frame-archive) | Edge-triggered capture that archives only flagged frames, prediction JSON, and Parquet roll-ups to B2 | [robot-log-offload](architectures/robot-log-offload/architecture.md) |
| [DuckDB Query In Place](https://github.com/backblaze-b2-samples/duckdb-query-in-place) | SQL over Parquet, CSV, and JSON on B2 with DuckDB httpfs, materializing results back to B2 | [fleet-search-replay](architectures/fleet-search-replay/architecture.md) |
| [B2 Event Broker](https://github.com/backblaze-b2-samples/b2-event-broker) | Fan-out of B2 Event Notifications to multiple subscribers | [robot-log-offload](architectures/robot-log-offload/architecture.md) |
| [WebDataset Streaming PyTorch Training](https://github.com/backblaze-b2-samples/webdataset-streaming-pytorch-training) | WebDataset tar shards streamed from B2 into a PyTorch IterableDataset, split by worker and node | [policy-training-registry](architectures/policy-training-registry/architecture.md) |
| [Ray Train/Tune checkpoints notebook](https://github.com/backblaze-b2-samples/notebooks/tree/main/ray-train-tune-checkpoints) | Ray Train and Tune checkpoints written to B2 persistent storage | [policy-training-registry](architectures/policy-training-registry/architecture.md) |
| [HF Cache Sync](https://github.com/backblaze-labs/hf-cache-sync) | Shared Hugging Face hub cache on B2 so trainers, CI, and robots pull base models once | [policy-training-registry](architectures/policy-training-registry/architecture.md) |
| [Mountpoint for S3 CSI driver with B2](https://github.com/backblaze-b2-samples/b2-integration-mountpoint-csi) | Read-mostly B2 bucket mounts in Kubernetes pods for jobs that expect file paths | [sim-rollout-datasets](architectures/sim-rollout-datasets/architecture.md), [policy-training-registry](architectures/policy-training-registry/architecture.md) |
<!-- catalog:samples:end -->

See the [full sample cross-reference](docs/related-b2-samples.md) for domain resources and selection guidance.

## B2 capability map

| Area | Capabilities | Selection notes |
|---|---|---|
| Access | S3 API, range GET, presigned GET/PUT/upload-part URLs, CORS, multipart, scoped keys (one bucket + one prefix + capabilities) | Robots and browsers get presigned URLs, never keys; a single presigned PUT or copy is limited to 5 GB |
| Change and lifecycle | Event Notifications, versions, lifecycle (hide, then delete), server-side copy, batch DeleteObjects (hides unless a VersionId is given) | Event Notifications are enabled by Backblaze Support; lifecycle cannot keep "the last K" objects |
| Protection | Object Lock (retention, legal hold), SSE-B2, Cloud Replication | Lock evidence and releases in dedicated buckets; replication is bucket-to-bucket DR, not fleet delivery |
| Delivery | Included egress, presigned GET, CDN and compute partners | Range reads for replay and multi-epoch streaming; see pricing for egress terms |
| Performance | Standard B2, [Overdrive](https://www.backblaze.com/cloud-storage/b2-overdrive), local cache | Standard by default; Overdrive for sustained multi-node training or bulk re-processing; local NVMe cache for repeated replays and epochs |

<!-- catalog:related:start -->
Other B2 reference architecture categories: [AI Data Providers](https://github.com/backblaze-b2-samples/b2-ai-data-provider-reference-architectures), [Generative Video](https://github.com/backblaze-b2-samples/b2-gen-video-reference-architectures), [Image Generation](https://github.com/backblaze-b2-samples/b2-image-generation-reference-architectures), [Autonomous Vehicles](https://github.com/backblaze-b2-samples/b2-autonomous-vehicle-reference-architectures), [Commercial Drones](https://github.com/backblaze-b2-samples/b2-commercial-drone-reference-architectures).
<!-- catalog:related:end -->

[Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage) is canonical for product behavior; this repository provides workflow-specific designs.

## Repository layout

`catalog/` architecture, integration and sample metadata, `schemas/` catalog schema, `architectures/` docs and diagrams, `docs/` agent-readable pages, `examples/` B2 configs and scoped keys, `skill/` portable agent skill, `tools/` generator and link checker, `tests/` tool tests, `metadata/` deployment templates, `.github/` CI and templates.

## Validate locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-catalog.txt pytest
python3 tools/generate_catalog.py --check
python3 tools/check_markdown_links.py            # add --external to probe outbound links
python3 -m pytest tests
```

## Contributing, security and license

See [CONTRIBUTING](.github/CONTRIBUTING.md); the catalog is the extension point. Report sensitive issues through the [security policy](.github/SECURITY.md). Released under the [MIT license](LICENSE); cite with [CITATION.cff](CITATION.cff).
