# Release Notes API — Secure Pipeline Demo

Companion demo for **Supply Chain Security Patterns for Cloud Delivery**, Module 1.
Scope: show the secured pipeline *working* — gates passing, gates blocking, and an
artifact promoted by digest into a running workload that fetches its secret at runtime.

## Architecture

```
GitHub (protected main)                              [source boundary]
   │  CodeConnections
   ▼
CodePipeline: release-notes-api-secure-release
   ├─ BuildAndVerify (CodeBuild)                     [dependency + build boundaries]
   │    Gate 1: gitleaks secret scan ......... BLOCKS
   │    Gate 2: pip-audit SCA on pinned deps . BLOCKS
   │    Gate 3: pytest ....................... BLOCKS
   │    docker build → syft SBOM → push to ECR (IMMUTABLE tags, scan-on-push)
   │    emits imageDetail.json (digest — the only reference used downstream)
   ├─ ScanGate (CodeBuild)                           [pre-production]
   │    Gate 4: policy-as-code on scan results
   │      CRITICAL → BLOCK   |   HIGH → WARN (recorded)
   ├─ ApproveRelease                                 [manual approval, with evidence]
   └─ Deploy (CodeBuild)                             [deploy boundary]
        Lambda updated to the exact image digest
        └─ workload fetches API key from Secrets Manager via execution role
```

No stored keys anywhere in the pipeline: every stage runs as a scoped IAM role
assumed at runtime — the AWS-native equivalent of the OIDC federation pattern
(Clip 4). The workload's own secret is retrieved at the moment of use (Clip 4,
slides 7–9).

## One-time setup (before recording)

1. **Repo.** Push `app/`, the three `buildspec-*.yml` files, and this README to a
   GitHub repo. Protect `main` (require PR review) so you can show the source
   boundary settings on camera.
2. **CodeConnections.** In the AWS console → Developer Tools → Connections, create
   a GitHub connection and click through the authorization (this one step cannot
   be automated). Copy its ARN.
3. **Stack.**
   ```bash
   aws cloudformation deploy \
     --stack-name secure-release-demo \
     --template-file infra/pipeline.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
       GitHubRepo=<owner>/<repo> \
       GitHubBranch=main \
       CodeConnectionArn=<connection-arn>
   ```
4. **Dry run.** Trigger one full execution and approve it end-to-end *before*
   recording. This warms everything (first Lambda create, ECR scan timing) and
   confirms the gates behave in your account. Run one break-the-build commit too.
5. Grab the function URL from the Deploy stage log output and keep it in a
   terminal ready to curl.

Costs are trivial (CodeBuild minutes + one 256 MB Lambda + one secret ≈ pennies),
but delete the stack after recording; `EmptyOnDelete` on the ECR repo makes
teardown clean.

## On-camera runbook (~2 pipeline runs)

**Run 1 — blocked release.** Commit the vulnerable `requests==2.19.1` pin
(`demo/break-the-build.md`). Show:
- Gate 2 failing in the CodeBuild log with the CVE IDs on screen
- Pipeline stopped at BuildAndVerify — **no artifact exists in ECR**
- The bad commit still in GitHub → your branching-strategy point

**Run 2 — clean release.** Revert, push. Show:
- The gate banners passing in sequence
- ECR: immutable tag, digest, scan-on-push findings page
- ScanGate log: the CRITICAL-blocks / HIGH-warns policy evaluation
- The approval action with evidence in the prompt; approve it deliberately
- Deploy log: "PROMOTING BY IMMUTABLE DIGEST"
- `curl <function-url>` → JSON shows the running digest and the masked,
  runtime-fetched API key

Timing note: a full clean run takes roughly 6–9 minutes (docker build + scan
poll). For a 6–10 minute clip, either trigger Run 2 first and narrate Run 1's
already-failed execution while Run 2 progresses, or cut between the two.

## What to say at each stage (concept mapping)

| Moment | Course concept |
|---|---|
| Branch protection settings | Source boundary: identity + integrity of the change |
| Pinned `requirements.txt` + pip-audit | Dependency boundary: provenance + byte-for-byte integrity |
| CodeBuild clean environment, SBOM | Build boundary: artifact honestly reflects approved inputs |
| Immutable ECR tag, digest in `imageDetail.json` | Artifact boundary: "latest" is a security problem |
| Scan gate policy output | Guardrails warn, gates block; block on fixable criticals |
| Manual approval with evidence | Approvals used sparingly, made meaningful |
| Deploy by digest | Deploy boundary: verify at the last possible moment |
| curl response, masked key | Secrets fetched at runtime, never baked in |
