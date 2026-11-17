# B2 configuration examples

Configuration templates for the buckets in these [reference architectures](../docs/architecture-index.md). Run command blocks from this repository's `examples/` directory using Bash and the B2 CLI v4. Authenticate the CLI with a provisioning credential before creating buckets or application keys. Configuration fields are documented in the [B2 API reference](https://www.backblaze.com/apidocs).

Set `ORG` to a globally unique bucket-name prefix. Set the additional variables used by the selected command block, and replace values shown in `<angle brackets>` before running it. Choose retention periods, lifecycle settings, and application-key capabilities for the workload; lifecycle rules permanently delete expired object versions.

| Variable | Purpose |
|---|---|
| `ORG` | Globally unique bucket-name prefix. |
| `DATASET` | Dataset identifier used to scope dataset prefixes. |
| `POLICY` | Policy identifier used to scope release reads. |
| `SIGNING_SECRET` | 32-character alphanumeric HMAC secret for the notification rule; store it in the webhook secret manager. |

| File | Applies to | Purpose | Architectures |
|---|---|---|---|
| `cors-viewers.json` | log bucket | Browser range reads of presigned MCAP and `.rrd` URLs from the Foxglove app and a Rerun Web Viewer origin | [fleet-search-replay](../architectures/fleet-search-replay/architecture.md) |
| `lifecycle-log-lake.json` | log bucket | Hide raw splits, `.rrd` recordings and edge-event frames after the retention window, then delete; also purges superseded versions from upload retries | [robot-log-offload](../architectures/robot-log-offload/architecture.md), [fleet-search-replay](../architectures/fleet-search-replay/architecture.md) |
| `lifecycle-scratch.json` | sim, mapping, training, datasets buckets | Expire scratch sweeps, unpromoted drafts and intermediate job outputs; purge hidden versions left by deletes under `rollouts/`, `scans/`, `maps/`, `trajectories/` and `checkpoints/` | [sim-rollout-datasets](../architectures/sim-rollout-datasets/architecture.md), [teleop-imitation-datasets](../architectures/teleop-imitation-datasets/architecture.md), [mapping-session-archive](../architectures/mapping-session-archive/architecture.md), [policy-training-registry](../architectures/policy-training-registry/architecture.md) |
| `object-lock-evidence.json` | evidence and release buckets | Default governance retention on incident evidence and released policies | [robot-log-offload](../architectures/robot-log-offload/architecture.md), [policy-training-registry](../architectures/policy-training-registry/architecture.md) |
| `event-notifications.json` | log bucket | Webhook on each new split under `bags/` to run the describe and catalog step | [robot-log-offload](../architectures/robot-log-offload/architecture.md) |

Retention periods are placeholders. Set them from your safety, contract and privacy obligations; lifecycle deletes data.
B2 lifecycle rules only hide and then delete by age per prefix. They do not tier storage and cannot keep "the last K" objects;
use the training framework for that (for example Ray Train `CheckpointConfig(num_to_keep=K)`).
Overlapping prefixes are allowed; B2 applies the smallest non-null value across matching rules, so `rollouts/scratch/` keeps its shorter windows.
An S3 `DeleteObject`/`DeleteObjects` call without a `VersionId` only hides the file on B2; its bytes stay stored until a
`daysFromHidingToDeleting` rule purges them or each version is deleted by `VersionId` (from `ListObjectVersions`, needs `deleteFiles`).

```bash
# Buckets: names are globally unique.
: "${ORG:?Set ORG to a globally unique prefix}"
b2 bucket create "$ORG-robot-logs" allPrivate
b2 bucket create "$ORG-robot-datasets" allPrivate
b2 bucket create "$ORG-robot-training" allPrivate
b2 bucket create "$ORG-robot-sim" allPrivate
b2 bucket create "$ORG-robot-mapping" allPrivate
b2 bucket create --file-lock-enabled "$ORG-robot-evidence" allPrivate
b2 bucket create --file-lock-enabled "$ORG-policy-releases" allPrivate

# Lifecycle, CORS, default retention
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-robot-datasets"
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-robot-training"
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-robot-sim"
b2 bucket update --lifecycle-rules "$(cat lifecycle-scratch.json)" "$ORG-robot-mapping"
b2 bucket update --lifecycle-rules "$(cat lifecycle-log-lake.json)" "$ORG-robot-logs"
b2 bucket update --cors-rules "$(cat cors-viewers.json)" "$ORG-robot-logs"
b2 bucket update --default-retention-mode governance --default-retention-period "365 days" "$ORG-robot-evidence"
b2 bucket update --default-retention-mode governance --default-retention-period "365 days" "$ORG-policy-releases"

# Event Notifications must be enabled for the account by Backblaze Support first.
# Then use b2_set_bucket_notification_rules with event-notifications.json, or:
: "${SIGNING_SECRET:?Set the notification HMAC signing secret}"
b2 bucket notification-rule create "b2://$ORG-robot-logs/bags/" describe-on-split \
  --event-type "b2:ObjectCreated:*" --webhook-url "https://hooks.example.com/b2/describe" --sign-secret "$SIGNING_SECRET"
```

## Scoped application keys

Each key below is restricted to one bucket, one name prefix, and the listed capabilities. Robots and browsers never hold
keys; they receive presigned URLs minted by a service that holds the key.

```bash
# Log offload and replay
b2 key create --bucket "$ORG-robot-logs" --name-prefix bags/    offload-signer   listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-robot-logs" --name-prefix catalog/ catalog-writer   listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-robot-logs" --name-prefix bags/    replay-signer    listFiles,readFiles
b2 key create --bucket "$ORG-robot-logs" --name-prefix rrd/     rrd-writer       listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-robot-logs" --name-prefix rrd/     rrd-signer       listFiles,readFiles
b2 key create --bucket "$ORG-robot-evidence" --name-prefix evidence/ evidence-writer \
  listFiles,readFiles,writeFiles,writeFileRetentions,writeFileLegalHolds,readFileRetentions,readFileLegalHolds

# Datasets, training and release (drafts/ and datasets/ are separate prefixes so the recorder cannot touch releases)
: "${DATASET:?Set DATASET before creating dataset keys}"
: "${POLICY:?Set POLICY before creating the release signer}"
b2 key create --bucket "$ORG-robot-datasets" --name-prefix "drafts/$DATASET/" recorder-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-robot-datasets" --name-prefix "drafts/$DATASET/" curator-reader listFiles,readFiles
b2 key create --bucket "$ORG-robot-datasets" --name-prefix "datasets/$DATASET/" curator-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-robot-datasets" --name-prefix "datasets/$DATASET/" trainer-reader listFiles,readFiles
b2 key create --bucket "$ORG-robot-training" --name-prefix checkpoints/ trainer-checkpoints listFiles,readFiles,writeFiles,deleteFiles
b2 key create --bucket "$ORG-policy-releases" --name-prefix models/ release-publisher listFiles,readFiles,writeFiles,writeFileRetentions
b2 key create --bucket "$ORG-policy-releases" --name-prefix "models/$POLICY/" release-signer listFiles,readFiles
```

A key holds one prefix, so the replay signer needs `replay-signer` and `rrd-signer`, and curation needs `curator-reader` and `curator-writer`.
`trainer-checkpoints` has `deleteFiles` because checkpoint pruning (for example Ray's `num_to_keep`) deletes old checkpoints.
A server-side copy into another bucket (log lake to evidence, checkpoints to releases) needs one key that can read the source
and write the destination. Single-bucket keys cannot do that, so the promotion step is the one exception to one-bucket keys: create a
short-lived key (`--duration`) covering both buckets (b2 v4.4.1 accepts a repeated `--bucket`), use it only in the promotion job,
and never widen a runtime key instead. A name prefix applies to every bucket on the key, and the source (`bags/`) and destination
(`evidence/`) prefixes differ, so this key carries no `--name-prefix` and can reach the whole of both buckets for its lifetime. Keep `--duration`
short, or rename the evidence prefix to share one with the source (for example copy `bags/...` to `bags/...` in the evidence bucket) and add `--name-prefix bags/`.

```bash
b2 key create --bucket "$ORG-robot-logs" --bucket "$ORG-robot-evidence" --duration 3600 evidence-promoter \
  listFiles,readFiles,writeFiles,writeFileRetentions,writeFileLegalHolds
```

`b2 key create` prints the secret once; store it in a gitignored `0600` `.env` or a secret manager, never in shell history or logs.
Bucket, lifecycle, CORS, retention and notification changes need an administrative key (or the master key), so run them once from
provisioning and keep that key out of runtime services.

## Object Lock and replication

Object Lock can be enabled at bucket creation or later, and cannot be disabled once enabled. Lifecycle rules do not delete
a file version that is still under retention or legal hold. B2 docs state that Object Lock cannot be enabled on a bucket that already
has a source replication rule; if you need DR copies of evidence or releases, enable Object Lock on both source and destination before
creating the rule ([Cloud Replication](https://www.backblaze.com/docs/cloud-storage-cloud-replication),
[Object Lock](https://www.backblaze.com/docs/cloud-storage-object-lock)). Cloud Replication is bucket-to-bucket DR, not fleet or customer delivery.
