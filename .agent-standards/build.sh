#!/usr/bin/env bash
# Regenerates a repo's AGENTS.md from these shared conventions plus its own
# repo-specific content. Run from the consuming repo's root:
#
#   .agent-standards/build.sh AGENTS.local.md AGENTS.md
#
# Re-run after editing SHARED.md (here) or the repo-specific file.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_FILE="${1:?usage: build.sh <local-file> [output-file]}"
OUTPUT_FILE="${2:-AGENTS.md}"

{
  echo "<!--"
  echo "GENERATED FILE. Do not edit directly."
  echo "Edit ${LOCAL_FILE} (repo-specific) or $(basename "${SCRIPT_DIR}")/SHARED.md (shared conventions),"
  echo "then regenerate with: $(basename "${SCRIPT_DIR}")/build.sh ${LOCAL_FILE} ${OUTPUT_FILE}"
  echo "-->"
  echo
  cat "${LOCAL_FILE}"
  echo
  cat "${SCRIPT_DIR}/SHARED.md"
} > "${OUTPUT_FILE}"

echo "Wrote ${OUTPUT_FILE}"