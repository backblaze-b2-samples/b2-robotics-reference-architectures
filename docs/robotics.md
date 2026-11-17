# Robotics on Backblaze B2 (agent-readable)

Catalog updated: 2026-11-16. Current product behavior is authoritative in the [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage).

## Workload
Robotics teams produce data at every stage. Fleets record rosbag2/MCAP logs sized by topic rates and recording duration, teleoperation produces demonstration datasets, simulation produces rollout sweeps, mobile robots produce LiDAR mapping sessions, and training produces multi-GB policy checkpoints. Most of it is written once, read many times by replay tools, dataloaders and trainers, and rarely deleted.

## Where does B2 fit?
B2 is the S3-compatible system of record behind that work: raw log lakes, versioned dataset releases, rollout sinks, checkpoint and policy release prefixes, and Object Lock evidence. Choose the connection method documented for each tool:

- **Built-in Backblaze B2 option:** MLflow (`b2://` artifact URI) and rclone (B2 backend).
- **S3 custom endpoint:** Ray Train, W&B, ClearML, Foxglove self-managed Primary Site (`s3_compatible`), DuckDB, DVC, Daft, Isaac Sim asset region profiles. Set the endpoint to `https://s3.<region>.backblazeb2.com`, derived from the bucket region.
- **fsspec / s3fs:** Zarr replay buffers through `s3fs.S3FileSystem(endpoint_url=...)`.
- **Presigned URLs:** browser viewers (the Foxglove app with remote files, the Rerun Web Viewer) take presigned GETs; robots upload with presigned PUTs.
- **S3 sync tool:** rosbag2, LeRobot, MuJoCo Playground, KISS-ICP and Open3D write local files; an offload agent, rclone or s5cmd moves closed files to and from B2. Backblaze samples ([Rosbag2 Cloud Offload](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload), [LeRobot B2 Streaming](https://github.com/backblaze-b2-samples/lerobot-b2-streaming), [MuJoCo Rollout Dataset](https://github.com/backblaze-b2-samples/mujoco-rollout-dataset), [KISS-ICP LiDAR Archive](https://github.com/backblaze-b2-samples/kiss-icp-lidar-archive), [Open3D Point Cloud Pipeline](https://github.com/backblaze-b2-samples/open3d-point-cloud-pipeline)) show the same flows written directly against the S3 API.

## Can I use B2 with ROS 2 rosbag2?
Yes. Record split MCAP files, presigned-PUT each closed split to `bags/<robot>/<session>/`, retain the local copy until the offload service verifies the uploaded version's size and full-file SHA-256. See [robot-log-offload](../architectures/robot-log-offload/architecture.md).

## Can I open B2 logs in Foxglove or Rerun?
Yes, with presigned GET URLs and bucket CORS rules for the viewer origin; Foxglove also requires range requests and no redirects. A self-managed Foxglove Primary Site uses B2 as its `s3_compatible` inbox and lake; configure a B2 Event Notification adapter that forwards object-created events to it. See [fleet-search-replay](../architectures/fleet-search-replay/architecture.md).

## Can I train from B2?
Yes. Ray Train, MLflow, W&B and ClearML document Backblaze B2 by name; trainers stream LeRobot v3 episodes or WebDataset shards with ranged GETs. See [teleop-imitation-datasets](../architectures/teleop-imitation-datasets/architecture.md) and [policy-training-registry](../architectures/policy-training-registry/architecture.md).

## B2 capabilities that apply
S3-compatible API; range GET; presigned GET, PUT and upload-part URLs; bucket CORS rules; multipart upload; application keys restricted to one bucket and one name prefix with listed capabilities; server-side copy (CopyObject, UploadPartCopy); batch DeleteObjects (without a VersionId it only hides files; purge with a lifecycle rule or delete by VersionId); lifecycle rules (hide, then delete, by age and prefix); Event Notifications (enabled by Backblaze Support on request; webhook, signed, at-least-once); Object Lock (governance or compliance, retention and legal hold); included egress (see [B2 pricing](https://www.backblaze.com/cloud-storage/pricing)).

## Reference architectures
- [robot-log-offload](../architectures/robot-log-offload/architecture.md): buckets `<org>-robot-logs` (`bags/`, `catalog/`, `events/`) and `<org>-robot-evidence` (Object Lock, `evidence/<incident_id>/`).
- [fleet-search-replay](../architectures/fleet-search-replay/architecture.md): DuckDB over `catalog/`, presigned GETs to Foxglove and Rerun, and presigned downloads for local `ros2 bag play`.
- [teleop-imitation-datasets](../architectures/teleop-imitation-datasets/architecture.md): drafts under `drafts/<name>/`, LeRobot v3 or Zarr releases under `datasets/<name>/<version>/`, curated with Daft, optionally tracked with DVC, streamed with ranged GETs.
- [sim-rollout-datasets](../architectures/sim-rollout-datasets/architecture.md): assets under `sim-assets/`, episodes under `rollouts/<env>/<policy>/<run_id>/`, promotion by server-side copy.
- [policy-training-registry](../architectures/policy-training-registry/architecture.md): `checkpoints/<run_id>/`, `eval/`, and an Object Lock release bucket `models/<policy>/<version>/`.
- [mapping-session-archive](../architectures/mapping-session-archive/architecture.md): `scans/`, `maps/`, `trajectories/`, `jobs/`, and approved `sitemaps/<site>/<version>/`.

## When Overdrive may apply
Sustained high-throughput reads where storage, not compute, is the bottleneck: many training nodes streaming one dataset version for long periods, or bulk re-processing of a large log lake. Interactive replay and fleet uploads (bounded by site uplinks) do not need it. Confirm with [Backblaze](https://www.backblaze.com/cloud-storage/b2-overdrive). For repeated epochs or replays of the same immutable data, a local NVMe cache is usually the first step.

## Where B2 does not fit
- The live ROS graph, DDS transport and real-time robot state.
- Partially written bags, HDF5 files and episodes; upload only closed files.
- Upload queues, tracking-server databases, search indexes, leaderboards and metrics time series.
- Simulator and GPU state, Ray object-store memory, training rendezvous.
- POSIX in-place edits and live USD collaboration.
- Fleet or customer delivery via Cloud Replication; replication is bucket-to-bucket DR.

## Links
[README](../README.md) - [Architecture index](architecture-index.md) - [Related B2 samples](related-b2-samples.md) - [Configuration examples](../examples/README.md) - [B2 docs](https://www.backblaze.com/docs/cloud-storage) - [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) - [B2 S3-compatible API](https://www.backblaze.com/docs/cloud-storage-s3-compatible-api) - [Event Notifications](https://www.backblaze.com/docs/cloud-storage-event-notifications) - [Object Lock](https://www.backblaze.com/docs/cloud-storage-object-lock)
