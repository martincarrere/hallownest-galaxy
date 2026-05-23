# Lore: Intentional Read/Write Asymmetry in Job Files API

**Related journal:** [[HG-2026-001-path-traversal-default-id-secret]]

## The Pattern

Some APIs enforce path/scope restrictions on writes but intentionally leave reads unrestricted.
This asymmetry is not always a bug it can be a deliberate design constraint.

## Why Galaxy Can't Restrict Reads

Galaxy job inputs (loc files, tool data tables) have **arbitrary paths** that vary per tool and
per installation. They cannot be enumerated the way job outputs can:

- **Write side**: job outputs are well-defined → restriction is feasible → `__check_job_can_write_to_path()` exists
- **Read side**: job inputs are unbounded → restriction was attempted and abandoned → no equivalent check

The maintainers confirmed this is by design: restricting reads would break legitimate job runner
functionality because legitimate tools reference files at paths that cannot be predicted.

## Takeaway for next Vuln Research

When you find a read/write asymmetry in an API:
1. Check if it is *intentional* (design constraint) or *accidental* (oversight)
2. Intentional asymmetry shifts the security burden elsewhere, find what that is (here: id_secret)
3. If the compensating control is weak or misconfigured, the intentional asymmetry becomes exploitable
