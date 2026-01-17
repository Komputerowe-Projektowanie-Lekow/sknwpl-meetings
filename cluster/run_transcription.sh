#!/bin/bash
set -euo pipefail

#===============================================================================
# Transcription Pipeline Submission Wrapper
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SBATCH_FILE="${SCRIPT_DIR}/transcription.sbatch"
LOG_DIR="${PROJECT_ROOT}/logs"

mkdir -p "${LOG_DIR}"

# Parse arguments
AUDIO_FILE="${1:-}"
MODEL="${2:-large-v3}"
LANGUAGE="${3:-pl}"

if [[ -z "$AUDIO_FILE" ]]; then
    echo "Usage: $0 <audio_file> [model] [language]"
    echo ""
    echo "Arguments:"
    echo "  audio_file  - Path to audio/video file"
    echo "  model       - Whisper model (default: large-v3)"
    echo "                Options: tiny, base, small, medium, large-v3"
    echo "  language    - Language code (default: pl)"
    echo ""
    echo "Examples:"
    echo "  $0 resources/audio/meeting.mkv"
    echo "  $0 resources/audio/meeting.mkv medium pl"
    exit 1
fi

if [[ ! -f "$AUDIO_FILE" ]]; then
    # Try relative to project root
    if [[ -f "$PROJECT_ROOT/$AUDIO_FILE" ]]; then
        AUDIO_FILE="$PROJECT_ROOT/$AUDIO_FILE"
    else
        echo "ERROR: Audio file not found: $AUDIO_FILE"
        exit 1
    fi
fi

# Get absolute path
AUDIO_FILE="$(realpath "$AUDIO_FILE")"

if [[ ! -f "${SBATCH_FILE}" ]]; then
    echo "ERROR: Sbatch file not found at ${SBATCH_FILE}"
    exit 1
fi

echo "=================================================="
echo " Submitting Transcription Job to SLURM"
echo "=================================================="
echo " Audio:    $AUDIO_FILE"
echo " Model:    $MODEL"
echo " Language: $LANGUAGE"
echo "=================================================="

# Submit with arguments
JOB_ID=$(sbatch --parsable "${SBATCH_FILE}" "$AUDIO_FILE" "$MODEL" "$LANGUAGE")

if [[ -z "${JOB_ID}" ]]; then
    echo "ERROR: Job submission failed."
    exit 1
fi

echo "Success! Job ID: ${JOB_ID}"
echo "Logs: ${LOG_DIR}/transcribe_${JOB_ID}.out"
echo "Monitor: squeue -j ${JOB_ID}"
echo "Results will be in: ~/sknwpl-meetings/results/transcribe_${JOB_ID}/"
echo "=================================================="
