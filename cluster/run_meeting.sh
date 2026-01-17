#!/bin/bash
set -euo pipefail

#===============================================================================
# Submit Full Meeting Pipeline to SLURM
#
# Usage:
#   ./run_meeting.sh <audio_file> [meeting_number] [date]
#
# Examples:
#   ./run_meeting.sh resources/audio/meeting.mkv
#   ./run_meeting.sh resources/audio/meeting.mkv 42
#   ./run_meeting.sh resources/audio/meeting.mkv 42 2026-01-17
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SBATCH_FILE="${SCRIPT_DIR}/full_pipeline.sbatch"
LOG_DIR="${PROJECT_ROOT}/logs"

# On ngpu cluster, use /export/ngpu path
if [[ -d "/export/ngpu/$USER" ]]; then
    CLUSTER_PROJECT_ROOT="/export/ngpu/$USER/sknwpl-meetings"
else
    CLUSTER_PROJECT_ROOT="$PROJECT_ROOT"
fi

mkdir -p "${LOG_DIR}"

# Parse arguments
AUDIO_FILE="${1:-}"
MEETING_NUMBER="${2:-}"
DATE="${3:-$(date +%Y-%m-%d)}"

if [[ -z "$AUDIO_FILE" ]]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     SKNWPL Meeting Pipeline - Submit to SLURM              ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    echo "║  Usage: ./run_meeting.sh <audio_file> [meeting#] [date]    ║"
    echo "║                                                            ║"
    echo "║  Examples:                                                 ║"
    echo "║    ./run_meeting.sh resources/audio/meeting.mkv            ║"
    echo "║    ./run_meeting.sh resources/audio/meeting.mkv 42         ║"
    echo "║                                                            ║"
    echo "║  This will:                                                ║"
    echo "║    1. Transcribe audio (GPU, large-v3 model)               ║"
    echo "║    2. Create video with SKNWPL background                  ║"
    echo "║    3. Upload to YouTube (unlisted)                         ║"
    echo "║    4. Save link to youtube_links.txt                       ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 1
fi

# Resolve audio file path
if [[ ! -f "$AUDIO_FILE" ]]; then
    if [[ -f "$PROJECT_ROOT/$AUDIO_FILE" ]]; then
        AUDIO_FILE="$PROJECT_ROOT/$AUDIO_FILE"
    else
        echo "ERROR: Audio file not found: $AUDIO_FILE"
        exit 1
    fi
fi

AUDIO_FILE="$(realpath "$AUDIO_FILE")"

if [[ ! -f "${SBATCH_FILE}" ]]; then
    echo "ERROR: Sbatch file not found at ${SBATCH_FILE}"
    exit 1
fi

# Check for YouTube credentials
CREDS_FILE="$CLUSTER_PROJECT_ROOT/credentials/youtube_token.pickle"
if [[ ! -f "$CREDS_FILE" ]]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ⚠️  WARNING: YouTube token not found!                      ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    echo "║  You need to generate OAuth token locally first:          ║"
    echo "║                                                            ║"
    echo "║    cd $PROJECT_ROOT"
    echo "║    python meeting.py upload some_video.mp4 --title test   ║"
    echo "║                                                            ║"
    echo "║  This opens browser for Google login and saves token.     ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Submitting Meeting Pipeline to SLURM                      ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Audio:   $(basename "$AUDIO_FILE")"
echo "║  Meeting: ${MEETING_NUMBER:-auto-increment}"
echo "║  Date:    $DATE"
echo "╚════════════════════════════════════════════════════════════╝"

# Submit with arguments
JOB_ID=$(sbatch --parsable "${SBATCH_FILE}" "$AUDIO_FILE" "$MEETING_NUMBER" "$DATE")

if [[ -z "${JOB_ID}" ]]; then
    echo "ERROR: Job submission failed."
    exit 1
fi

echo ""
echo "✅ Job submitted!"
echo "   Job ID: ${JOB_ID}"
echo "   Logs:   ${LOG_DIR}/meeting_${JOB_ID}.out"
echo ""
echo "Monitor:  squeue -j ${JOB_ID}"
echo "Results:  $CLUSTER_PROJECT_ROOT/results/"
echo "Links:    $CLUSTER_PROJECT_ROOT/youtube_links.txt"
