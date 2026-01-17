#!/bin/bash
set -euo pipefail

#===============================================================================
# Install Transcription Environment (one-time setup)
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SBATCH_FILE="${SCRIPT_DIR}/install_transcription_env.sbatch"
LOG_DIR="${PROJECT_ROOT}/logs"

mkdir -p "${LOG_DIR}"

if [[ ! -f "${SBATCH_FILE}" ]]; then
    echo "ERROR: Sbatch file not found at ${SBATCH_FILE}"
    exit 1
fi

echo "Submitting environment installation job to SLURM (partition: ngpu)..."
JOB_ID=$(sbatch --parsable "${SBATCH_FILE}")

echo "Submitted Job ID: ${JOB_ID}"
echo "Logs: ${LOG_DIR}/transcribe_${JOB_ID}.out"
echo "Wait for this job to finish before running transcription."
