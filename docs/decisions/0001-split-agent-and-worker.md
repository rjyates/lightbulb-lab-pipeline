# 0001. Split the Claude agent from a credentialed deterministic worker

- **Status:** Proposed
- **Date:** 2026-10-28

## Context
Lightbulb Lab should research, produce, publish and improve with minimal owner attention, using the existing Claude Pro subscription and no paid API credits. Claude Code cloud scheduled tasks can run unattended, but they start from a fresh clone, share the owner's subscription usage, can be rejected at usage limits, and act with the owner's GitHub identity, so GitHub branch protection cannot stop them. Rendering is CPU-heavy and needs voice and YouTube credentials. See the [proposal](../autonomy/proposal.md).

## Options considered
1. **Agent does everything in the cloud** (render and upload from scheduled tasks). Pros: one system. Cons: credentials in a cloud environment reachable by a prompt-injectable agent; ephemeral disk; heavy renders consume subscription usage; publishing stops whenever usage runs out.
2. **Everything on the owner's machine with `claude -p`.** Pros: local files. Cons: the same agent still holds credentials; depends on one machine for thinking as well as producing.
3. **Split: cloud agent proposes through Git; a deterministic worker on the owner's own computer (Windows since 2026-10-28) holds credentials, gates and publishes from a buffered queue, running only owner-signed code for protected paths.** Pros: credentials and policy enforcement stay out of the agent's reach; usage limits only delay new work; gates are testable code. Cons: two components to maintain; the owner must manage a signing key.
4. **Render in GitHub Actions.** Free for public repos, but production secrets would sit in workflows that agent PRs can modify.

## Decision
Option 3. The agent works only through branches, PRs, issues and the private ops repository. The worker deploys owner-signed tags (later also `main` when no protected path changed), makes no LLM calls, and enforces the signed policy, rate limits and endpoint allowlists in code.

## Consequences
- A mistaken or manipulated agent can produce at most a bad PR, which CI and the worker's gates must catch.
- Gate, policy and publishing code change only with the owner's signature; low-risk fixes elsewhere can ship automatically after M8.
- Publishing continues from the buffer when Claude runs fail or hit limits.
- Requires: a private ops repo, a signing key, a worker computer that is on for some hours each week, and a test suite before any automation is trusted.
- Revisit if Anthropic offers scoped bot identities for scheduled tasks, or if the worker host becomes unreliable.
