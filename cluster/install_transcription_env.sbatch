#!/bin/bash
#SBATCH -J transcribe
#SBATCH -A adsimml
#SBATCH -p ngpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH -o /home/%u/sknwpl-meetings/logs/transcribe_%j.out
#SBATCH -e /home/%u/sknwpl-meetings/logs/transcribe_%j.err

#===============================================================================
# Transcription Environment Setup Script (one-time)
#===============================================================================

cleanup() {
    EXIT_CODE=$?
    echo "=== SETUP FINISHED (Exit Code: $EXIT_CODE) ==="
}
trap cleanup EXIT

echo "JOB STARTED on $(hostname)"
echo "Date: $(date)"

# Project root
PROJECT_ROOT="$HOME/sknwpl-meetings"
mkdir -p "$PROJECT_ROOT/logs"

# 1. Setup Conda
CONDA_PATH="$HOME/miniconda3/etc/profile.d/conda.sh"

if [[ ! -f "$CONDA_PATH" ]]; then
    echo "Conda not found at $CONDA_PATH. Trying alternatives..."
    if [[ -d "$HOME/anaconda3" ]]; then
        CONDA_PATH="$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [[ -d "$HOME/opt/miniconda3" ]]; then
        CONDA_PATH="$HOME/opt/miniconda3/etc/profile.d/conda.sh"
    fi
fi

if [[ -f "$CONDA_PATH" ]]; then
    source "$CONDA_PATH"
else
    echo "ERROR: Could not find conda.sh"
    exit 1
fi

echo "Conda init successful."

# 2. Check if environment exists
ENV_NAME="whisper"
if conda info --envs | grep -qE "^${ENV_NAME}\s"; then
    echo "Environment '${ENV_NAME}' already exists. Skipping creation."
    echo "If you want to reinstall: conda env remove -n ${ENV_NAME}"
    exit 0
else
    echo "Creating environment '${ENV_NAME}'..."
    conda create -n ${ENV_NAME} -c conda-forge python=3.11 pip ffmpeg -y
fi

# 3. Install faster-whisper with CUDA support
echo "Activating '${ENV_NAME}'..."
conda activate ${ENV_NAME}

echo "Installing faster-whisper with CUDA support..."
pip install faster-whisper psutil

# Install CUDA dependencies for CTranslate2
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

# Install YouTube upload dependencies
echo "Installing YouTube API dependencies..."
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client pyperclip

# 4. Verify installations
echo "Verifying installation..."

# Check faster-whisper
python -c "from faster_whisper import WhisperModel; print('✅ faster-whisper OK')"

# Check ffmpeg
if command -v ffmpeg &>/dev/null; then
    echo "✅ ffmpeg OK: $(ffmpeg -version | head -1)"
else
    echo "⚠️ ffmpeg not found in PATH, trying to install..."
    conda install -c conda-forge ffmpeg -y
fi

# Check YouTube API
python -c "from googleapiclient.discovery import build; print('✅ YouTube API OK')"

if [[ $? -eq 0 ]]; then
    echo ""
    echo "=========================================="
    echo "SUCCESS: Environment ready!"
    echo "=========================================="
    echo "Environment: ${ENV_NAME}"
    echo ""
    echo "Next steps:"
    echo "  1. Copy youtube_token.pickle to cluster"
    echo "  2. Run: ./cluster/run_meeting.sh <audio_file>"
    echo "=========================================="
else
    echo "ERROR: Installation verification failed."
    exit 1
fi

echo "Setup complete."
