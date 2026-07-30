# Personal-machine stats pipeline

Fetches WhoScored's League/UCL/Europa/World Cup player stats, aggregates them
into a ranked summary, and writes it to the stats S3 bucket - from this
machine's residential IP.

This is the only path that produces the app's rankings. It replaced an AWS
Lambda + Step Functions pipeline whose fetch step could never work
(WhoScored/Cloudflare answers AWS's egress IPs with a flat 403); that pipeline
has since been deleted, and `infra/` now holds only the S3 bucket and the SNS
alert topic this script uses.

The Django app's read path (`api/services/s3_summary_service.py`) needs no
changes - it only ever reads `summary/latest_summary.json`.

## One-time setup

### 1. Create a dedicated least-privilege IAM user

Don't reuse the broad `default`/`admin` AWS profiles for this. Create a new
IAM user scoped to exactly what this script needs. The `s3:ListBucket`
statement is required even though the script only ever does `GetObject`/
`PutObject`: without it, a `GetObject` on a key that doesn't exist yet (e.g.
`summary/latest_manifest.json` before the very first run) returns a
misleading `AccessDenied` instead of `NoSuchKey` - S3 won't tell an identity
without list permission whether an object is actually missing or just
inaccessible. Confirmed live: the first real run failed with exactly this
error until the `ListBucket` statement was added.

```bash
aws iam create-user --user-name bdor-stats-pipeline-script --profile default

cat > /tmp/bdor-stats-pipeline-script-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListForMissingKeyLookups",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::bdor-stats-dev",
      "Condition": {"StringLike": {"s3:prefix": ["raw/*", "summary/*"]}}
    },
    {"Sid": "RawWrite", "Effect": "Allow", "Action": "s3:PutObject", "Resource": "arn:aws:s3:::bdor-stats-dev/raw/*"},
    {"Sid": "SummaryReadWrite", "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": "arn:aws:s3:::bdor-stats-dev/summary/*"},
    {"Sid": "PublishAlerts", "Effect": "Allow", "Action": "sns:Publish", "Resource": "arn:aws:sns:us-east-1:741448927703:bdor-stats-pipeline-alerts-dev"}
  ]
}
EOF

aws iam put-user-policy \
  --user-name bdor-stats-pipeline-script \
  --policy-name bdor-stats-pipeline-script-policy \
  --policy-document file:///tmp/bdor-stats-pipeline-script-policy.json \
  --profile default

aws iam create-access-key --user-name bdor-stats-pipeline-script --profile default
```

Take the `AccessKeyId`/`SecretAccessKey` from that last command's output and add
a new profile:

```bash
aws configure set aws_access_key_id     <AccessKeyId>     --profile bdor-stats-script
aws configure set aws_secret_access_key <SecretAccessKey> --profile bdor-stats-script
aws configure set region                us-east-1         --profile bdor-stats-script
```

### 2. Configure the script

```bash
cp scripts/stats_pipeline/.env.example scripts/stats_pipeline/.env
```

Edit `scripts/stats_pipeline/.env` and fill in `STATS_URL` (copy the value from
the repo root's `.env` - there's no shared config linking the two files, so
keep them in sync by hand if it ever changes). The other defaults should be
correct as-is.

### 3. Run it once manually

```bash
cd /home/bmwodoame/Desktop/MyEnvironment/bdor
uv run python -m scripts.stats_pipeline
```

Check `logs/stats_pipeline.log` for a clean `status=200` line per source. Run
it again immediately - it should log "Not due yet" and exit without
refetching (the cadence gate working).

### 4. Install the cron job

```bash
crontab -e
```

Add (keeping any existing lines untouched):

```cron
0 * * * * cd /home/bmwodoame/Desktop/MyEnvironment/bdor && /home/bmwodoame/.local/bin/uv run python -m scripts.stats_pipeline >> logs/cron_stdout.log 2>&1
```

Runs hourly, but the script itself only actually fetches roughly every 2 days
(`FETCH_INTERVAL_DAYS` in `.env`) - most hourly ticks just check
`summary/latest_manifest.json` and exit immediately. This also means a
transient failure, or the machine being off/asleep at any single moment,
gets retried within the hour instead of losing a full ~2-day cycle.

`uv`'s absolute path is hardcoded above because cron's minimal environment
doesn't source `.bashrc`/`.profile`, so `~/.local/bin` may not be on `PATH`.
Confirm with `which uv` if you've installed it somewhere else.

## Failure alerting

On any failure, the script publishes to the SNS topic the stack creates
(`AlertTopic` in `infra/template.yaml`, subscribed to the address configured
when the stack was deployed) - no separate alerting setup needed. This is the
only alerting for the pipeline: the CloudWatch alarms that watched the old
Lambda pipeline's executions and 403s were deleted with it, and this script's
logs live on this machine rather than in CloudWatch. The ARN is hardcoded in
`.env` rather than looked up live; update it if the stack is ever redeployed
under a different `Stage`, account, or region.

## Logs

- `logs/stats_pipeline.log` - the script's own rotating log (5MB × 5 backups).
- `logs/cron_stdout.log` - catches anything printed before Python's own
  logging is configured (e.g. `uv` itself failing, import errors).

Both are gitignored (`logs/` in the repo root `.gitignore`).

## Credential rotation

If you ever rotate the `bdor-stats-pipeline-script` IAM user's access key,
regenerate it (`aws iam create-access-key`), update the `bdor-stats-script`
AWS profile (`aws configure set ... --profile bdor-stats-script`), and delete
the old key (`aws iam delete-access-key`) - no script changes needed.
