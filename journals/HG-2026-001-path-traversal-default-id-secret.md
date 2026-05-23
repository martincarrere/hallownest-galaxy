### Summary

1) CWE-22: Path Traversal

 The Galaxy upload file feature is vulnerable to Path Traversal. While the write feature implements the protection of the file path while the the read endpoint index() has no check.

2) CWE-1188: Insecure Default id_secret

The setting ` id_secret` is declared as `required: false` with no startup validation. Galaxy
starts silently with this insecure default if the operator never sets it in
galaxy.yml and the id_secret configuration value defaults to the static, publicly known string


**In summary we can combined this two attacks these two vulnerablities:**

**Precondition**: the target instance must be running the default `id_secret`. On instances where a custom secret is configured, Vulnerability 1 still exists but exploiting it requires independent knowledge of the secret, which is not demonstrated in this report.

On any Galaxy installation where id_secret has never been explicitly set:

  1. Attacker self-registers a standard Galaxy account (no admin access needed)
  2. Attacker submits a job to obtain a valid encoded job ID
  3. Attacker forges a valid job_key using the known default id_secret
     and Galaxy's IdEncodingHelper (HMAC derivation)
  4. Attacker calls:
         ```GET /api/jobs/{job_id}/files?job_key=FORGED&path=AnyFileReadableByGalaxyLinuxUser```
  5. Server responds HTTP 200 and returns the full file contents

From galaxy.yml the attacker obtains the master API key, database credentials,
and any other configured secrets which lead to full compromise of the instance.

- exfiltration of SSH private keys
- Access to files stored on disk
- Exfiltration of all user datasets or corporate datasets
- Read of /etc/passwd and other system files

### Details

#### VULNERABILITY 1:  CWE-22: Path Traversal

File : galaxy/webapps/galaxy/api/job_files.py
Endpoint : GET /api/jobs/{job_id}/files

**Description**

The GET /api/jobs/{job_id}/files endpoint (JobFilesAPIController.index) opens
any path supplied by the caller without validating that it belongs to the
requesting job.

The write endpoint create() correctly restricts paths via:
```
    __check_job_can_write_to_path(trans, job, path)

    if not in_work_dir and not self.__is_output_dataset_path(job, path):
        raise exceptions.ItemAccessibilityException(
            "Job is not authorized to write to supplied path."
        )
```

The read endpoint index() has no **equivalent check**. This asymmetry is the core
flaw: any caller with a valid job_key can read any file accessible by the
Galaxy process, regardless of whether it belongs to their job.

**https://github.com/galaxyproject/galaxy/blob/32fab9a2a92200123472915931128c48c68405ef/lib/galaxy/webapps/galaxy/api/job_files.py#L63**


#### VULNERABILITY 2: CWE-1188: Insecure Default id_secret

All installations where id_secret is not explicitly set in galaxy.yml
The id_secret configuration value defaults to the static, publicly known string:

[galaxy.yml.sample](https://github.com/galaxyproject/galaxy/blob/32fab9a2a92200123472915931128c48c68405ef/lib/galaxy/config/sample/galaxy.yml.sample#L2082)

The setting is declared as required: false with no startup validation. Galaxy
starts silently without blocking with this insecure default if the operator never sets it in
galaxy.yml, with no warning displayed at runtime.

Since id_secret is used to derive job_key values via HMAC, an attacker who
knows the default can forge valid job_key values for any job ID without any
prior credentials.

### PoC

Full script: [spells/HG-2026-001-path-traversal-default-id-secret.py](../spells/HG-2026-001-path-traversal-default-id-secret.py)

### Impact

- On instances running the default `id_secret`: turns Vulnerability 1 into a fully unauthenticated remote exploit with no credentials required
- Affects misconfigured installations that have never explicitly set `id_secret`
- Default is publicly documented, no bruteforce required
- Where a custom secret is in use, Vulnerability 1 remains present but `id_secret` recovery is out of scope for this report

### Remediation

- Warn at startup when `id_secret` matches a known insecure default — no operator should miss it
- Disable the job_files endpoint by default; enable only when Pulsar is configured
- Long term: auto-generate a random secret when none is set, with care for integration compatibility