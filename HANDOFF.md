# ChronoLab — Handoff

**Request Bedrock model access before anything else** (AWS Console → Bedrock →
Model access → request the vision-capable and text models). It needs approval
and can take time — nothing else here is blocked on it, so kick it off first.

This doc is written for a tired person at 11pm. Copy-paste the commands in
order. Every step tells you what "it worked" looks like.

---

## 1. Clone and configure

```bash
git clone <repo-url> && cd chronolab
cp .env.example .env
```

Open `.env` and fill in **only the block at the top** marked `FILL THESE IN
BY HAND` — everything below it gets written automatically by `bootstrap.sh`.

| Variable | Example | What it is |
|---|---|---|
| `AWS_MODE` | `cloud` | Use `cloud` for the real deploy. `local` only runs against LocalStack/moto with no AWS account. |
| `AWS_REGION` | `ap-south-1` | Region for S3, DynamoDB, EC2, Cognito, AVP. |
| `BEDROCK_REGION` | `ap-south-1` | Only change this if your Bedrock model access was granted in a *different* region than `AWS_REGION` — check the Bedrock console's Model access page. |
| `RESOURCE_SUFFIX` | `nj` | Your initials or any short unique string. S3 bucket names are globally unique across all of AWS, so this can't be blank. |

You also need the AWS CLI installed and configured:

```bash
aws configure
aws sts get-caller-identity
```

**Expected output:** a JSON block with your `Account`, `UserId`, and `Arn`. If
this errors, nothing else will work — fix it first (see Troubleshooting).

---

## 2. Run bootstrap

```bash
./scripts/bootstrap.sh
```

This is the **only** script that creates AWS infrastructure. It is safe to
re-run — every step checks before it creates, so if it fails partway through,
just run it again.

**Expected output**, roughly in this order:
1. `Preflight OK — AWS CLI present, credentials valid.`
2. `Bedrock model access confirmed.` — if this fails, see Troubleshooting.
3. S3 bucket + DynamoDB table created.
4. Cognito user pool + app client + two test users created.
5. Verified Permissions policy store + identity source + both Cedar policies loaded.
6. IAM role/instance profile, security group, key pair created.
7. EC2 `t3.small` launched — this step takes a minute or two (waits for the instance to reach "running").
8. Amplify app + branch created.
9. A final summary block printing the bucket name, table name, Cognito pool ID, app client ID, policy store ID, and **both test users' login credentials**.

**Test logins** (both created by bootstrap.sh, passwords come from your `.env` — the defaults in `.env.example` are `ChangeMe123!`, change them before a real demo):

| Role | Username | What it demonstrates |
|---|---|---|
| Doctor | value of `COGNITO_DOCTOR_USERNAME` | Can view any patient's records, insights, add medications, export FHIR. |
| Patient | value of `COGNITO_PATIENT_USERNAME` | Can only view records for `COGNITO_PATIENT_ID` (default `PT-1002`) — try requesting `PT-1001`'s data while logged in as this user and you should get a 403 with a `determining_policies` field naming the Cedar policy that blocked it. This is the demo's key shot. |

---

## 3. Run deploy

```bash
./scripts/deploy.sh
```

Builds the backend Docker image, ships it to the EC2 instance over SSH, and
pushes a fresh frontend build to Amplify. Unlike `bootstrap.sh`, this only
touches application code, never infrastructure — safe to re-run any time you
push a change.

**Expected output:**
1. Docker build completes.
2. Image copied to EC2, loaded, `docker compose up -d` runs.
3. A health-check line: `http://<your-ec2-dns>/ -> 200` (or similar).
4. Frontend build completes, zip uploaded to Amplify, a `Deployment started
   (job <id>)` line, and the Amplify URL printed at the end.

The Amplify deployment takes a minute or two to go live after this script
finishes — check the URL it prints, or the Amplify console, for status.

---

## 4. Stop the EC2 instance after the demo

**This is not optional — it bills while running (~$15–17/month), even idle,
unlike Fargate it does not scale to zero.**

```bash
aws ec2 stop-instances --instance-ids $(grep '^EC2_INSTANCE_ID=' .env | cut -d= -f2) --region $(grep '^AWS_REGION=' .env | cut -d= -f2)
```

To fully tear everything down instead of just stopping the instance, see
`scripts/teardown.sh`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Bedrock model access check failed` | Model access not yet approved, or approved in a different region | Check the Bedrock console's Model access page for the exact region; update `BEDROCK_REGION` in `.env` if needed; re-run `bootstrap.sh`. |
| `BucketAlreadyExists` / bucket creation fails | Someone else already owns that exact bucket name (S3 names are global) | Change `RESOURCE_SUFFIX` in `.env` to something more unique, re-run. |
| Everything 403s with region-related errors | `AWS_REGION` doesn't match where your resources actually live (e.g. ran bootstrap.sh twice with different regions) | Check `.env`'s generated ARNs match `AWS_REGION`; if they don't, you likely need to start over with a fresh `RESOURCE_SUFFIX`. |
| `aws sts get-caller-identity` fails | CLI not configured | Run `aws configure` and paste in an access key/secret from an IAM user with sufficient permissions. |
| Caddy shows a certificate error / site doesn't load over HTTPS | DNS hasn't propagated yet, or `DUCKDNS_DOMAIN`/`DUCKDNS_TOKEN` weren't set before `bootstrap.sh` ran | Wait a few minutes for DNS propagation; confirm `https://<your-duckdns-domain>` resolves to the EC2 IP (`dig` or [whatsmydns.net](https://www.whatsmydns.net)); if you set DuckDNS vars *after* running bootstrap.sh, re-run it so it points DuckDNS at the instance. |
| WebSocket / real-time updates don't work in the browser | The frontend is served over HTTPS (Amplify) but tried to open `ws://` instead of `wss://` — browsers block this | Confirm `VITE_WS_BASE_URL` in `.env` is `wss://` not `ws://` before the frontend build; re-run `scripts/deploy.sh`. |
| Login succeeds but every API call 403s with an empty `determining_policies` | AVP's Cognito identity source may not be mapping `custom:role`/`custom:patient_id` token claims to principal attributes the way the Cedar policies expect (this is a genuinely untested assumption — see `progress.txt`) | Decode the ID token at jwt.io and confirm `custom:role`/`custom:patient_id` claims are present; use the AVP console's policy store "test bench" to check what principal attributes it actually sees. |

---

## What each script owns

- `scripts/bootstrap.sh` — creates infrastructure. Idempotent. Run it whenever `.env`'s human-fill block changes or a previous run failed partway.
- `scripts/deploy.sh` — pushes application code (backend image + frontend build). Run it every time you want to ship a code change.
- `scripts/teardown.sh` — deletes everything `bootstrap.sh` created, in reverse order. Run it when you're done and want a clean account.
