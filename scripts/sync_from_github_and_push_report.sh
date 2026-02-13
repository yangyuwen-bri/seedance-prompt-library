#!/usr/bin/env bash
set -Eeuo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/data"
LOG_DIR="${ROOT_DIR}/logs"
REPORT_DIR="${ROOT_DIR}/reports"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
LOG_FILE="${LOG_DIR}/github_sync_job_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/daily_report_${TIMESTAMP}.md"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
OPENCLAW_BIN="${OPENCLAW_BIN:-$(command -v openclaw || true)}"

TELEGRAM_CHANNEL="${TELEGRAM_CHANNEL:-telegram}"
TELEGRAM_TARGET="${TELEGRAM_TARGET:--1003791213002}"
GITHUB_PROMPT_LIBRARY_URL="${GITHUB_PROMPT_LIBRARY_URL:-https://raw.githubusercontent.com/yangyuwen-bri/seedance-prompt-library/main/data/prompt_library.json}"

mkdir -p "${LOG_DIR}" "${REPORT_DIR}" "${DATA_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[$(date '+%F %T')] Seedance GitHub sync job started"
echo "LOG_FILE=${LOG_FILE}"
echo "GITHUB_PROMPT_LIBRARY_URL=${GITHUB_PROMPT_LIBRARY_URL}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 not found"
  exit 1
fi

TMP_FILE="${DATA_DIR}/prompt_library.json.tmp"
TARGET_FILE="${DATA_DIR}/prompt_library.json"

curl -fsSL "${GITHUB_PROMPT_LIBRARY_URL}" -o "${TMP_FILE}"
"${PYTHON_BIN}" -m json.tool "${TMP_FILE}" >/dev/null
mv "${TMP_FILE}" "${TARGET_FILE}"
echo "Updated local data file: ${TARGET_FILE}"

cd "${ROOT_DIR}"
"${PYTHON_BIN}" scripts/generate_daily_report.py --output "${REPORT_FILE}"
echo "Report written: ${REPORT_FILE}"

if [[ "${SKIP_TELEGRAM_PUSH:-0}" == "1" ]]; then
  echo "SKIP_TELEGRAM_PUSH=1, skipping Telegram delivery"
  exit 0
fi

if [[ -z "${OPENCLAW_BIN}" ]]; then
  echo "openclaw not found, cannot deliver report to Telegram"
  exit 1
fi

MESSAGE="$(cat "${REPORT_FILE}")"

"${OPENCLAW_BIN}" message send \
  --channel "${TELEGRAM_CHANNEL}" \
  --target "${TELEGRAM_TARGET}" \
  --message "${MESSAGE}"

echo "[$(date '+%F %T')] Seedance GitHub sync job completed"
