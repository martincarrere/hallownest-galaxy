# Lore: Attack Surface Reduction When a Feature Depends on a Single Secret

**Related journal:** [[HG-2026-001-path-traversal-default-id-secret]]

## The Pattern

When a feature's entire security model rests on a single shared secret, the right mitigation
is not just "make the secret strong" — it is to minimize who ever needs the feature at all.

## Galaxy's Approach for job_files API

The job_files endpoint security is entirely dependent on `id_secret`.
Since restricting reads is infeasible (see [[HG-LORE-job-files-read-write-asymmetry]]),
the maintainers chose attack surface reduction:

- **Disable the endpoint by default** — only enable it when Pulsar (the remote job runner) is in use
- **Give admins an explicit off-switch** — diligent admins can disable it entirely even when Pulsar is present

This does not fix the root issue but drastically limits exposure:
most Galaxy instances do not use Pulsar → most instances no longer expose the endpoint at all.

## Takeaway for Vuln Research / Remediation Advice

When a feature cannot be secured from the inside (unbounded inputs, can't enumerate valid paths):
1. Propose disabling it by default — force an explicit opt-in
2. Pair with a runtime warning if a weak/default secret is detected
3. Document the blast radius clearly: who needs this feature vs. who has it silently enabled

This is also useful for writing impact sections: if the endpoint were disabled by default,
the attack would require two misconfigurations (Pulsar enabled + default id_secret) instead of one.
