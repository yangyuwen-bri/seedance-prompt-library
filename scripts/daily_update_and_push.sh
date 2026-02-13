#!/usr/bin/env bash
set -Eeuo pipefail

# Keep a predictable PATH for cron jobs.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
REPORT_DIR="${ROOT_DIR}/reports"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
LOG_FILE="${LOG_DIR}/daily_job_${TIMESTAMP}.log"
REPORT_FILE="${REPORT_DIR}/daily_report_${TIMESTAMP}.md"

# Export variables from .env if present.
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

OPENCLAW_BIN="${OPENCLAW_BIN:-$(command -v openclaw || true)}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
TELEGRAM_CHANNEL="${TELEGRAM_CHANNEL:-telegram}"
TELEGRAM_TARGET="${TELEGRAM_TARGET:--1003791213002}"

DAYS_BACK="${DAYS_BACK:-2}"
MAX_ITEMS="${MAX_ITEMS:-4000}"

mkdir -p "${LOG_DIR}" "${REPORT_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[$(date '+%F %T')] Seedance daily job started"
echo "ROOT_DIR=${ROOT_DIR}"
echo "LOG_FILE=${LOG_FILE}"

# Legacy system-cron entry guard:
# keep this job disabled by default to avoid duplicate runs with OpenClaw cron.
if [[ "${ENABLE_SYSTEM_CRON_JOB:-0}" != "1" ]]; then
  echo "ENABLE_SYSTEM_CRON_JOB is not 1, exiting without execution."
  exit 0
fi

cd "${ROOT_DIR}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 not found"
  exit 1
fi

if [[ "${SKIP_PIPELINE:-0}" != "1" ]]; then
  "${PYTHON_BIN}" scripts/run_pipeline.py --days "${DAYS_BACK}" --max "${MAX_ITEMS}"
else
  echo "SKIP_PIPELINE=1, skipping scripts/run_pipeline.py"
fi

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
MESSAGE+=$'\n\n'
MESSAGE+="本地报告文件: ${REPORT_FILE}"

"${OPENCLAW_BIN}" message send \
  --channel "${TELEGRAM_CHANNEL}" \
  --target "${TELEGRAM_TARGET}" \
  --message "${MESSAGE}"

echo "[$(date '+%F %T')] Seedance daily job completed"
