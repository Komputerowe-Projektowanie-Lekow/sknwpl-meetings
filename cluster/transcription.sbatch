#!/bin/bash
#SBATCH -J transcribe
#SBATCH -A adsimml
#SBATCH -p ngpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o /home/%u/sknwpl-meetings/logs/transcribe_%j.out
#SBATCH -e /home/%u/sknwpl-meetings/logs/transcribe_%j.err

#===============================================================================
# Transcription Pipeline on SLURM (GPU)
#===============================================================================

# --- TRAP & LOG RECOVERY ---
cleanup() {
    EXIT_CODE=$?
    echo ""
    echo "=== CLEANUP (Exit Code: $EXIT_CODE) ==="
    
    # Copy results from scratch if exists
    if [[ -n "$SCRATCH_DIR" && -d "$SCRATCH_DIR" && -d "$OUTPUT_DIR" ]]; then
       echo "Copying results from scratch..."
       rsync -a "$SCRATCH_DIR/output/" "$OUTPUT_DIR/"
    fi
}
trap cleanup EXIT

# 0. Parse arguments
AUDIO_FILE="${1:-}"
if [[ -z "$AUDIO_FILE" ]]; then
    echo "ERROR: No audio file specified."
    echo "Usage: sbatch transcription.sbatch <audio_file> [model] [language]"
    exit 1
fi

MODEL="${2:-large-v3}"
LANGUAGE="${3:-pl}"

echo "JOB STARTED on $(hostname)"
echo "Date: $(date)"
echo "Audio: $AUDIO_FILE"
echo "Model: $MODEL"
echo "Language: $LANGUAGE"

# Project root
PROJECT_ROOT="$HOME/sknwpl-meetings"
mkdir -p "$PROJECT_ROOT/logs"

# 1. Setup Scratch
SCRATCH_DIR="/raid/$USER/transcribe_${SLURM_JOB_ID}"
mkdir -p "$SCRATCH_DIR/output"
echo "Scratch: $SCRATCH_DIR"

# Copy audio to scratch
AUDIO_BASENAME=$(basename "$AUDIO_FILE")
cp "$AUDIO_FILE" "$SCRATCH_DIR/$AUDIO_BASENAME"

# 2. Activate Environment
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
echo "GPU Info:"
nvidia-smi --query-gpu=name,memory.total --format=csv

# 3. Run Transcription
echo "--- Starting Transcription ---"
cd "$SCRATCH_DIR"

python - <<EOF
import sys
sys.path.insert(0, "$PROJECT_ROOT/src")
from transcript_tools.transcription import transcribe_with_faster_whisper

result = transcribe_with_faster_whisper(
    "$SCRATCH_DIR/$AUDIO_BASENAME",
    model_size="$MODEL",
    language="$LANGUAGE",
    output_dir="$SCRATCH_DIR/output",
    device="cuda",
    compute_type="float16",
    batch_size=16,
)

print(f"Duration: {result['duration_formatted']}")
print(f"Segments: {len(result['segments'])}")
print(f"Words: ~{len(result['full_text'].split())}")
EOF

# 4. Copy Results
OUTPUT_DIR="$PROJECT_ROOT/results/transcribe_${SLURM_JOB_ID}"
mkdir -p "$OUTPUT_DIR"

echo "--- Copying results to $OUTPUT_DIR ---"
rsync -a "$SCRATCH_DIR/output/" "$OUTPUT_DIR/"

# List output files
echo "Output files:"
ls -la "$OUTPUT_DIR/"

# 5. Cleanup scratch
echo "--- Cleaning up scratch ---"
rm -rf "$SCRATCH_DIR"

echo "SUCCESS"
echo "Results in: $OUTPUT_DIR"
