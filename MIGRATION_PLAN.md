# ChronoLab — Build It → Ship It Migration Plan

**Purpose:** migrate ChronoLab from a fully emulated local stack (LocalStack + Ollama + a hand-rolled Cedar check) to a deployed AWS architecture with a public URL, without adding features or breaking the working demo.

**Audience:** the implementing coding agent. Read the whole file before starting.

> ### ⚠️ Read this first: there are two people
>
> **The builder** (no AWS account) writes all the code and all the infrastructure scripts, testing against LocalStack.
>
> **The account owner** (a teammate, has the AWS account and the credits) runs the result. He gets the project late and must not have to debug it.
>
> **The design constraint for every task below:** the account owner edits **one `.env` file** and runs **one script**. Nothing else. If a task would require him to click through a console, open a Python file, or paste an ARN somewhere, it has been done wrong — make it a scripted step instead. See **Phase 9 — Handoff**.

---

## ⏱ 24-HOUR MODE — read this before anything else

**Scope is Phases 0–4 only.** Phases 5–8 are cut unless Phase 4 finishes with hours to spare. Do not start any stretch phase without checking the clock against the budget below first.

### Hour budget (adjust to your actual start time, but keep the ratios)

| Hours | Do |
|---|---|
| 0–1 | Phase 0. Message the account owner **now** — Bedrock approval and EC2 access are the two things you cannot speed up yourself. |
| 1–4 | Phase 1 (config layer + real S3/DynamoDB), building against LocalStack in parallel so you're not blocked on the account. |
| 4–9 | Phase 2 (Bedrock). Start the moment access is confirmed, not before — don't burn time writing Bedrock code you can't test yet. |
| 9–14 | Phase 3 (Cognito + AVP). Highest value per hour of anything in the plan — protect this window. |
| 14–20 | Phase 4 (EC2 deploy). This is the phase most likely to run long; see the checkpoint below. |
| 20–24 | Video, writeup, submission. **Not negotiable — a working app with no video scores nothing.** Stop building at hour 20 even if Phase 4 isn't fully polished. |

### 🚨 Hard checkpoint at hour 12

If **Bedrock access hasn't come through** or **the account owner hasn't gotten you EC2/IAM access** by hour 12:

- **Stop waiting on the cloud.** Fall back to `AWS_MODE=local` (LocalStack + Ollama) for the remainder.
- Redirect all remaining time into **Phase 3 only** — Cognito/AVP has no dependency on Bedrock or on the live account being reachable; it just needs *an* AWS surface, and LocalStack won't cover AVP, so at minimum get the real Cognito pool + AVP policy store created (that part just needs account access, not Bedrock) and wire it into the still-local app.
- A LocalStack demo with **real Cedar evaluation** and a clear "here's what Ship It would add" slide in the writeup beats a half-broken cloud deploy filmed in a panic. Judges score what runs, not what was attempted.

### What this means for the phases below

- Every "stretch" label now means **do not attempt**, full stop, unless Phase 4 is done with 3+ hours still on the clock.
- Skip the rehearsal step in Phase 9 that says "the day before" — you don't have a day before. Rehearse Phase 0's bootstrap stub the moment it exists, not at the end.
- The account owner should be looped in for hour 0–1 and hour 14 (right before the EC2 phase), not just handed a finished repo at hour 20.

---

## 0. Ground rules

These override any instinct to improve things.

1. **No new features.** Every task below either (a) replaces an emulated component with a real one, or (b) makes an *existing* feature visible in the demo. If you find yourself adding functionality, stop and re-read this line.
2. **The app must run end to end after every phase.** Never leave the repo in a state where the demo is broken. Commit at every checkpoint with a descriptive message.
3. **No credentials in code or in git.** Local dev uses an AWS profile; deployed code uses IAM roles. Never bake an access key into the container or a `.env` that gets committed. Add `.env` to `.gitignore` if it isn't already.
4. **Fallbacks must be loud.** Every fallback path logs at `WARNING` and sets a flag the UI can surface. The current silent `llava:7b → qwen2.5:3b` fallback is a bug, not a feature — fix it as part of Phase 2.
5. **Keep the LocalStack path alive** behind a config flag. It is both a writeup line ("same code, two environments") and a 2am safety net if the network dies.
6. **Synthetic patient data only.** No real medical reports on a live cloud account, at any point.
7. **Nothing account-specific may be hardcoded, anywhere.** No account IDs, ARNs, region strings, bucket names, user pool IDs or policy store IDs in Python, JSON, YAML or frontend code. All of it reads from config. Before every commit, run:
   ```bash
   grep -rInE '[0-9]{12}|arn:aws|ap-south-1|us-east-1|chronolab-pdfs|localhost:8000' \
     --include='*.py' --include='*.js' --include='*.jsx' --include='*.json' . \
     | grep -v node_modules
   ```
   Any hit outside `config.py`, `.env.example` or the bootstrap script is a bug.
8. **Infrastructure is a script, not console clicks.** Every "create the bucket / table / user pool / policy store / IAM role" instruction below means *write it into `scripts/bootstrap.sh`*, not *click it in the console*. The account owner will never reproduce your clicks.

### Priority order if time runs out

Do not reorder. Cut from the bottom. **In 24-hour mode, treat everything below Phase 4 as already cut** — see the box above.

| Priority | Phase | Why |
|---|---|---|
| Must | 0 — Prep | Blocks everything |
| Must | 1 — Real S3 + DynamoDB | Core AWS claim |
| Must | 2 — Bedrock | Core AWS claim |
| **Must** | **3 — Cognito + Verified Permissions** | **Converts the weakest claim into the strongest. Never cut this.** |
| Must | 4 — Deploy | Ship It requires a URL |
| Stretch | 5 — Event-driven pipeline | Best single video shot |
| Stretch | 6 — Bedrock Guardrails | Enforces the safety differentiator |
| Should | 7 — Proof tasks | Makes existing work visible |
| Must | 8 — Submission hygiene | Scored directly |
| **Must** | **9 — Handoff** | **Built incrementally throughout, not at the end. Nothing runs without it.** |

---

## Phase 0 — Prep (blocks everything; start now)

### 0a. Account owner — send him this list TODAY

These are the only things no script can do for him, and two of them have lead times measured in hours or days. Message him before writing any code.

- [ ] Create the AWS account, apply the credits.
- [ ] **Set a budget alarm at $20 and $50.** (The bootstrap script also does this, but belt and braces — this account has his card on it.)
- [ ] **Request Bedrock model access** in the console for the vision-capable and text models. **This needs approval and can take time. It is the single biggest schedule risk in the project.** Nothing else blocks on it, so it must be requested first.
- [ ] Report back: **account ID, chosen region, and whether the Bedrock models are available there.**
- [ ] Install the AWS CLI and confirm `aws sts get-caller-identity` works.

### 0b. Builder — start immediately, in parallel

- [ ] Assume `ap-south-1` for S3/DynamoDB/compute, and make it a variable regardless. If the Bedrock models aren't in Mumbai, the config must support a **separate Bedrock region** (e.g. `us-east-1`) while data services stay local — **note this latency/data-residency tradeoff in the writeup**, since Ship It explicitly scores architecture decisions.
- [ ] Write `backend/requirements.txt` (currently missing — this blocks every deploy). Pin versions.
- [ ] Fix the PyMuPDF `fitz` deprecation import.
- [ ] Create `.env.example`, committed, with **every** variable documented by comment, and a clearly marked block at the top for the handful of values a human must supply:
  ```bash
  # ─── FILL THESE IN BY HAND (everything below is generated by bootstrap.sh) ───
  AWS_MODE=cloud
  AWS_REGION=ap-south-1
  BEDROCK_REGION=ap-south-1       # change if model access is in another region
  RESOURCE_SUFFIX=               # your initials or any short unique string
  # ─────────────────────────────────────────────────────────────────────────────
  ```
  Keep this block to **four or five lines**. Everything else gets generated.
- [ ] Add `.env` to `.gitignore`.
- [ ] Create `scripts/bootstrap.sh` as a stub now. Every later phase appends to it.

**Checkpoint:** account owner has been messaged, `.env.example` exists, bootstrap stub exists, app still runs locally on LocalStack + Ollama.

---

## Phase 1 — Config layer, then real S3 and DynamoDB

The boto3 code should barely change. `endpoint_url` is the only real difference between LocalStack and the real thing.

- [ ] Create `backend/config.py` exposing a single `AWS_MODE` env var with values `local` | `cloud`, and **one factory function** that returns boto3 clients.
  - In `local`: inject `endpoint_url` pointing at LocalStack, use test credentials.
  - In `cloud`: omit `endpoint_url` entirely, rely on the credential chain.
- [ ] **Refactor every module to get clients from that factory.** No other file constructs a boto3 client directly. Check at minimum `server.py`, `pipeline.py`, `demo_script.py`, `auth_middleware.py`.
- [ ] **In `scripts/bootstrap.sh`**, add: create S3 bucket `chronolab-pdfs-${RESOURCE_SUFFIX}` (block all public access, versioning on) and DynamoDB table `chronolab-records-${RESOURCE_SUFFIX}` (PK `patient_id`, SK `record_id`, **on-demand billing**).
  > **S3 bucket names are globally unique.** Plain `chronolab-pdfs` may already be taken in someone else's account — the suffix is not optional.
- [ ] The script **writes the resulting names into `.env`**. The app reads them from there; it never constructs them.
- [ ] Make the script **idempotent**: check-then-create at every step, so a half-failed run can simply be re-run. Assume it *will* fail partway on the first real attempt.
- [ ] Run `demo_script.py` against LocalStack via the same script path. The `put_object` and `KeyConditionExpression` calls should be unchanged.

**Checkpoint:** `AWS_MODE=local` and `AWS_MODE=cloud` differ only by `.env`. Bootstrap runs clean against LocalStack twice in a row.

> **Video asset:** screenshot the DynamoDB table showing real items now.

---

## Phase 2 — Bedrock replaces Ollama

- [ ] Add a provider abstraction in `pipeline.py`:
  - An interface with `extract_from_image(...)` and `canonicalize(...)`.
  - Two implementations: `OllamaProvider` and `BedrockProvider`, selected by config.
  - **Do not rewrite the pipeline logic.** Phase A and Phase B keep their current shape, prompts and JSON contracts.
- [ ] Use the **Bedrock Converse API**, not raw `InvokeModel`. It gives a uniform message/image interface and makes swapping models a config change.
- [ ] **Port Phase A (extraction):** page rendered to image → image content block → same strict-JSON instruction → same output schema `{test_name, raw_value, raw_unit, date, reference_range}`.
- [ ] **Port Phase B (canonicalization):** same fixed vocabulary (HbA1c, Fasting Glucose, Total Cholesterol, LDL Cholesterol), `temperature 0.1`, JSON-only output.
- [ ] **Move unit-conversion maths out of the model and into Python** if any of it currently lives in the prompt. The `mmol/mol → %` and `mmol/L → mg/dL` conversions are deterministic and must never be delegated to an LLM. Add unit tests for them.
- [ ] Keep the confidence score and the `< 0.7` low-confidence threshold exactly as they are.
- [ ] Add retry with exponential backoff on Bedrock throttling exceptions. You will be throttled.
- [ ] **Fix the silent fallback:** any fallback (vision → text extraction, Bedrock → Ollama) must log at `WARNING` and set a field on the record that the UI can display.

**Checkpoint:** full pipeline on Bedrock. Run a known report through both providers and **diff the canonical output** — investigate any difference before moving on.

---

## Phase 3 — Cognito + Verified Permissions replace the Cedar mock

**This is the highest-value phase.** Amazon Verified Permissions is managed Cedar, so the existing policy text is mostly reusable. Today `auth_middleware.py` holds a Cedar-*shaped* string and evaluates it with hand-rolled logic; no Cedar engine runs. That is the one claim in the repo a judge could read as overstated, and it sits on the project's differentiator.

> **All of this goes in `scripts/bootstrap.sh`.** The pool ID, client ID and policy store ID are generated per account — they must be captured by the script and written into `.env`, never pasted into code.

- [ ] **Cognito user pool** with at least two users: a doctor, and a patient. Add custom attributes `role` and `patient_id` so they appear as token claims. Seed both users with passwords read from `.env` (defaulted in `.env.example`, changeable), so the account owner can log in without console work.
- [ ] **Create an AVP policy store.** Start non-validating to move fast; add a schema only if time allows.
- [ ] Keep the policies as **`.cedar` files in the repo**, loaded by the script. Do not embed policy text in Python.
- [ ] Load **two** policies:
  1. **Doctor:** permitted to view records, view insights, add medications, export FHIR.
  2. **Patient:** permitted to view records **only where `principal.patient_id == resource.patient_id`**.

  > Policy 2 is the whole point. A string comparison cannot express it, and it is what gives the demo teeth.
- [ ] Rewrite `auth_middleware.py`:
  - **Keep the `@requires_auth()` decorator signature** so no route code changes.
  - Inside, call **`IsAuthorizedWithToken`** — it accepts the Cognito token directly, saving you from writing JWT validation.
  - Map each route to an `(action, resource)` pair.
  - **On denial, return the decision and the matching policy ID** in the response body. This is what makes the video shot legible.
- [ ] **Delete the mock policy string.** Do not comment it out.
- [ ] Frontend: add a login screen, store the token, attach it to all API requests **and to the WebSocket connect**.

**Checkpoint:** log in as the patient for `PT-1002`, request `PT-1001`'s timeline, receive a denial produced by a real policy engine, with the policy ID shown.

> **Video asset:** film this denial.

---

## Phase 4 — Deploy (EC2 + Docker)

> **Deliberate choice: a single EC2 instance running Docker, not ECS Fargate.**
> Nobody on the team has used ECS, and Fargate's first-time setup (ECR + task definition + cluster + service + two IAM roles + ALB + target groups + security groups + subnets) is where a day disappears, usually to a networking failure that looks like "container starts, then dies, no logs". Judges score *whether it works*, not the compute layer — the architecture story here is carried by Bedrock, Verified Permissions, DynamoDB and Step Functions.
>
> **Do not use App Runner** either: its WebSocket support is the known risk, and `/ws/timeline/{patient_id}` is load-bearing for the multiplayer demo.
>
> **Still containerize.** Docker is what makes the deploy reproducible and the handoff a one-liner — and it's an honest writeup line. You are just running the container on a box you can SSH into.

### Backend

- [ ] Dockerize the FastAPI backend: non-root user, pinned `requirements.txt`, `.dockerignore`.
- [ ] Test the image locally first — `docker run` with `AWS_MODE=local` against LocalStack must work before it ever touches EC2.
- [ ] **In `scripts/bootstrap.sh`**, add EC2 provisioning:
  - Launch a **`t3.small`** (Amazon Linux 2023). `t3.micro` is too tight once Docker plus the Python image is running.
  - **Security group:** inbound 80 and 443 from anywhere, 22 from anywhere (hackathon-acceptable; note it as a known shortcut in the writeup rather than pretending otherwise). Nothing else.
  - **Attach an IAM instance profile** scoped to exactly: the one S3 bucket, the one DynamoDB table, the specific Bedrock model ARNs, and the AVP policy store. Build ARNs in the script from account ID and region — never hardcoded, no wildcards. **This is the one thing not to simplify away** — it keeps the least-privilege story intact and means no access keys ever touch the box.
  - **User-data script** on first boot: install Docker, enable it, pull/run the image, install Caddy.
  - Write the resulting public IP/DNS into `.env`.
- [ ] **Caddy in front** for TLS and WebSocket proxying. Caddy gets a certificate automatically and proxies WebSocket upgrades with no extra config, which is why it's worth the five minutes over raw nginx. A free subdomain (DuckDNS or similar) pointed at the instance IP gives Caddy a hostname to issue a certificate for.
  > HTTPS is not optional: Amplify serves the frontend over HTTPS, and a browser will block `ws://` from an `https://` page. Without TLS the multiplayer demo dies in the browser console.
- [ ] `scripts/deploy.sh`: build image → copy to the instance (or push to ECR and pull) → `docker compose up -d`. One command for the account owner.

### Frontend

- [ ] Deploy to **Amplify Hosting**.
- [ ] **Replace the hardcoded `localhost:8000`** with a build-time environment variable.
- [ ] Fix CORS to allow the Amplify domain, and check the WebSocket origin separately — CORS config does not cover WebSocket upgrades.
- [ ] Verify end to end from a phone and from a signed-out browser.

### Cost note

- [ ] A `t3.small` is roughly **$15–17/month on demand** and is *not* covered by the always-free tier, so it burns credits while idle. **Tell the account owner to stop the instance after the demo** — put it in `HANDOFF.md`. Unlike Fargate, this does not scale to zero.

**Checkpoint:** a working public HTTPS URL, WebSockets included. **In 24-hour mode, this is the finish line — go straight to Phase 8 (submission hygiene) from here, not Phase 5.**

---

## Phase 5 — Event-driven pipeline *(stretch — skip in 24-hour mode)*

Only start this if Phases 0–4 are complete and stable. This converts a script into an architecture.

- [ ] Enable EventBridge notifications on the S3 bucket.
- [ ] EventBridge rule starts a **Step Functions** state machine: Phase A → Phase B → DynamoDB write.
  - Retry with backoff on the LLM steps.
  - A catch branch writing failures to a dead-letter location.
- [ ] Simplest implementation: two Lambda **container images** reusing the same `pipeline.py` provider code — do not duplicate the logic. Watch the Lambda timeout and give them generous memory.
- [ ] The FastAPI upload route becomes "put to S3 and return"; the WebSocket broadcasts completion.

> **Video asset:** the Step Functions execution graph lighting up green is the best single shot available to you.

---

## Phase 6 — Bedrock Guardrails *(stretch — skip in 24-hour mode)*

The current prompts *ask* the model not to diagnose ("if you violate these rules, the system will fail"). That is a request, not an enforcement.

- [ ] Create a Guardrail with denied topics: diagnosis, treatment efficacy, prognosis.
- [ ] Attach it to the `/api/chat` and Doctor Insights Bedrock calls via the Converse guardrail config.
- [ ] **Keep the existing system prompts** as the first layer. Defence in depth.

> **Video asset:** ask "does my father have diabetes?" on camera and let the guardrail block it.

---

## Phase 7 — Proof, not features *(only if Phase 4 finishes early)*

Existing work that is currently invisible. Do these in order, as time allows. **In 24-hour mode, item 2 (unit-conversion) is the only one worth squeezing in if you have a spare 30 minutes** — it's the cheapest and it's your best technical story.

- [ ] **Provenance.** Click a timeline point → view the source PDF page it came from. The page number is already captured in Phase A; this is mostly a presigned S3 URL and a modal.
- [ ] **The unit-conversion save.** Prepare two synthetic reports for the same test, in *different units*, from *different labs*. Show them landing on one continuous line. This is the strongest technical idea in the project and it currently appears nowhere in the UI.
- [ ] **Confidence in action.** One deliberately ambiguous report → low-confidence dot → "Needs Review" badge → a human correcting it.

---

## Phase 8 — Submission hygiene

- [ ] **Synthetic data only** — verify no real reports reached the live account.
- [ ] Update `IMPLEMENTATION_PLAN.md` and `BACKEND_STRUCTURE.md` to match reality, **or delete them**. Stale docs listing old routes and schema names look worse than no docs.
- [ ] Validate the FHIR bundle if you are going to claim FHIR export.
- [ ] Writeup must cover: the problem, the build, **where AWS fits**, **the AI coding tools used** (required by the rules), and a **per-report cost figure** (Ship It scores cost decisions and almost nobody will bother).
- [ ] **Demo video, under 3 minutes.** Suggested shot list:
  1. The problem (~20s)
  2. Two labs' differing units merging into one continuous line
  3. Step Functions execution graph *(if Phase 5 done)*
  4. The AVP policy denial, with policy ID
  5. The guardrail refusing a diagnostic question *(if Phase 6 done)*
  6. FHIR export
- [ ] Upload unlisted to YouTube, then **open the link in a signed-out browser** before submitting.
- [ ] Public repo, submission form, before the deadline.

> **Rules reminder:** if the video does not show it, it does not count. A feature that exists only in the writeup scores nothing.

---

## Phase 9 — Handoff

**Build this incrementally as you go.** It is not an end-of-project task; if you leave it to the last night, it will not work.

### The contract

The account owner does exactly this, and nothing more:

```bash
git clone <repo> && cd chronolab
cp .env.example .env
$EDITOR .env                    # fills in 4-5 lines at the top
./scripts/bootstrap.sh          # creates everything, appends generated IDs to .env
./scripts/deploy.sh             # builds, pushes, deploys
```

If any step requires him to open a console, read an ARN off a screen, or edit a `.py` file, **the handoff has failed** — fix the script instead.

### `scripts/bootstrap.sh` requirements

- [ ] **Step 1, before anything that can cost money: create the budget alarm.** He is running your script against an account with his card attached. Put it first, and say so in a comment he'll see while reading. This is what makes the script trustworthy enough to run.
- [ ] **Preflight checks before any creation:** AWS CLI present, `sts get-caller-identity` succeeds, required `.env` vars non-empty, **Bedrock model access confirmed** (make a single tiny inference call and fail loudly with a clear message if it's not granted). Catching this in preflight instead of halfway through a deploy saves an hour.
- [ ] **Idempotent throughout.** Check-then-create. Re-running after a failure must be safe.
- [ ] **Appends generated values to `.env`**: bucket name, table name, user pool ID, app client ID, policy store ID, role ARNs, ECR repo URI.
- [ ] **Echo a clear summary at the end**: what was created, the login credentials for both test users, and what to run next.
- [ ] Optional but worth it: a `scripts/teardown.sh`. He may want his account clean afterwards, and offering it makes running the bootstrap an easier decision.

### `HANDOFF.md` (committed at repo root)

Written **for a tired person at 11pm**. Commands, not prose.

- [ ] The exact command sequence above, in order.
- [ ] **Expected output after each step**, so he knows whether it worked.
- [ ] The 4–5 `.env` values he must supply, with an example of each.
- [ ] Both test users' credentials and what each one demonstrates.
- [ ] A short troubleshooting table: Bedrock access denied, bucket name taken, region mismatch, CLI not configured, Caddy certificate not issued yet (DNS not propagated), WebSocket blocked (page on HTTPS, socket on `ws://`).
- [ ] **"Stop the EC2 instance after the demo"** — with the exact command. It bills while idle.
- [ ] One line at the top: **"Request Bedrock model access before anything else — it needs approval and may take time."**

### Rehearse it (compressed — no spare day here)

- [ ] Skip a separate "day before" run. Instead: **the first time `bootstrap.sh` reaches a runnable state (end of Phase 1), immediately run it once against LocalStack from a clean `.env`.** Fix anything that breaks right then, not later.
- [ ] Do one real dry run against the live account **as early in Phase 3 or 4 as the account is reachable** — that's the only way to catch account-specific failures LocalStack can't reproduce (IAM propagation delays, model access, quotas). Waiting until hour 20 to discover an IAM propagation delay is how the video doesn't get made.

---

## Cut list, in order

**In 24-hour mode, items 1 and 2 below are already cut by default** — see the 24-HOUR MODE box at the top. This list only matters if you finish Phase 4 with hours to spare.

1. Phase 5 (event-driven pipeline)
2. Phase 6 (Guardrails)
3. WebSocket multiplayer — **from the video only**, keep the code
4. Either Doctor Insights or the chat widget from the video — whichever demos worse (they overlap conceptually)

**Never cut Phase 3.** Real Cedar evaluation is the difference between a claim and a demonstration. If hour 12 arrives and the cloud isn't working, Phase 3 running against real Cognito/AVP with the rest of the app on LocalStack is a legitimate submission — a broken cloud deploy is not.

**Never cut Phase 9's handoff basics** (bootstrap script, `.env.example`, one summary doc) **or Phase 8's video/writeup.** Perfect code nobody can run, or a working app with no video, both score zero. If the clock forces a choice, cut a feature before you cut either of these.
