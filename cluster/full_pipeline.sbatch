#!/bin/bash
#SBATCH -J sknwpl_meeting
#SBATCH -A adsimml
#SBATCH -p ngpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o /home/%u/sknwpl-meetings/logs/meeting_%j.out
#SBATCH -e /home/%u/sknwpl-meetings/logs/meeting_%j.err

#===============================================================================
# SKNWPL Full Meeting Pipeline on SLURM
# 
# Automates: Transcription → Video → YouTube Upload → Save Link
#
# REQUIREMENTS:
# 1. Run install_transcription_env.sbatch first (one-time)
# 2. YouTube OAuth token must be generated locally first:
#    python meeting.py upload test.mp4 --title "test"
#    (This creates credentials/youtube_token.pickle)
#===============================================================================

set -euo pipefail

# --- TRAP & LOG RECOVERY ---
cleanup() {
    EXIT_CODE=$?
    echo ""
    echo "=== CLEANUP (Exit Code: $EXIT_CODE) ==="
    
    # Copy results from scratch if exists
    if [[ -n "${SCRATCH_DIR:-}" && -d "${SCRATCH_DIR:-}" ]]; then
       echo "Copying any remaining files from scratch..."
       rsync -a "$SCRATCH_DIR/" "$PROJECT_ROOT/results/scratch_backup_${SLURM_JOB_ID}/" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# 0. Parse arguments
AUDIO_FILE="${1:-}"
MEETING_NUMBER="${2:-}"
DATE="${3:-$(date +%Y-%m-%d)}"

if [[ -z "$AUDIO_FILE" ]]; then
    echo "ERROR: No audio file specified."
    echo "Usage: sbatch full_pipeline.sbatch <audio_file> [meeting_number] [date]"
    echo ""
    echo "Examples:"
    echo "  sbatch full_pipeline.sbatch resources/audio/meeting.mkv"
    echo "  sbatch full_pipeline.sbatch resources/audio/meeting.mkv 42"
    echo "  sbatch full_pipeline.sbatch resources/audio/meeting.mkv 42 2026-01-17"
    exit 1
fi

echo "=========================================="
echo "SKNWPL Full Meeting Pipeline"
echo "=========================================="
echo "JOB ID:  $SLURM_JOB_ID"
echo "HOST:    $(hostname)"
echo "DATE:    $(date)"
echo "AUDIO:   $AUDIO_FILE"
echo "MEETING: ${MEETING_NUMBER:-auto}"
echo "=========================================="

# Project root - compute nodes use /home
PROJECT_ROOT="$HOME/sknwpl-meetings"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/results"

# 1. Setup Scratch
SCRATCH_DIR="/raid/$USER/meeting_${SLURM_JOB_ID}"
mkdir -p "$SCRATCH_DIR"
echo "Scratch: $SCRATCH_DIR"

# Copy audio to scratch
if [[ ! -f "$AUDIO_FILE" ]]; then
    # Try relative to project root
    if [[ -f "$PROJECT_ROOT/$AUDIO_FILE" ]]; then
        AUDIO_FILE="$PROJECT_ROOT/$AUDIO_FILE"
    else
        echo "ERROR: Audio file not found: $AUDIO_FILE"
        exit 1
    fi
fi

AUDIO_BASENAME=$(basename "$AUDIO_FILE")
echo "Copying audio to scratch..."
cp "$AUDIO_FILE" "$SCRATCH_DIR/$AUDIO_BASENAME"

# Copy background image
cp "$PROJECT_ROOT/resources/templates/pmarlo_background.png" "$SCRATCH_DIR/" 2>/dev/null || {
    echo "WARNING: Background image not found, using placeholder"
    # Create a simple placeholder image using ImageMagick if available
    convert -size 1920x1080 xc:#1a1a2e -fill white -gravity center \
        -pointsize 72 -annotate 0 "SKNWPL" "$SCRATCH_DIR/pmarlo_background.png" 2>/dev/null || \
    echo "Could not create placeholder"
}

# 2. Activate Environment
echo "--- Activating Conda Environment ---"
# Try $HOME path (works on compute nodes)
CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"
source "$CONDA_PATH" || {
    echo "ERROR: Conda source failed"
    exit 1
}
conda activate whisper || {
    echo "ERROR: Could not activate whisper environment"
    echo "Run install_transcription_env.sbatch first!"
    exit 1
}

# Check GPU
echo "--- GPU Info ---"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv

# 3. Run Full Pipeline
echo ""
echo "=========================================="
echo "Starting Full Pipeline"
echo "=========================================="
cd "$SCRATCH_DIR"

# Build command
PIPELINE_CMD="python $PROJECT_ROOT/cluster/full_pipeline.py"
PIPELINE_CMD+=" '$SCRATCH_DIR/$AUDIO_BASENAME'"
PIPELINE_CMD+=" --device cuda"
PIPELINE_CMD+=" --model large-v3"
PIPELINE_CMD+=" --date $DATE"

if [[ -n "$MEETING_NUMBER" ]]; then
    PIPELINE_CMD+=" --meeting-number $MEETING_NUMBER"
fi

echo "Running: $PIPELINE_CMD"
eval $PIPELINE_CMD

# 4. Copy Results
echo ""
echo "--- Copying Results ---"
# Results are already saved by full_pipeline.py to PROJECT_ROOT/results/

# 5. Cleanup scratch
echo "--- Cleaning up scratch ---"
rm -rf "$SCRATCH_DIR"

echo ""
echo "=========================================="
echo "SUCCESS!"
echo "=========================================="
echo "Check results in: $PROJECT_ROOT/results/"
echo "YouTube links in: $PROJECT_ROOT/youtube_links.txt"
echo "=========================================="
