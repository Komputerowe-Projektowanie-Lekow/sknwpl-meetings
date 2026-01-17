#!/usr/bin/env python3
"""
Full Meeting Pipeline - End-to-End Processing

Automates: Transcription → Video Creation → YouTube Upload → Save Link
No manual ChatGPT steps needed.

Usage:
    python full_pipeline.py <audio_file> [--meeting-number N] [--date YYYY-MM-DD]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcript_tools.transcription import transcribe_with_faster_whisper
from transcript_tools.audio_to_video import create_video_from_audio
from transcript_tools.upload_youtube import upload_video, generate_meeting_description

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
BACKGROUND_IMAGE = RESOURCES_DIR / "templates" / "pmarlo_background.png"
YOUTUBE_LINKS_FILE = PROJECT_ROOT / "youtube_links.txt"


def get_next_meeting_number() -> int:
    """Get next meeting number from youtube_links.txt."""
    if not YOUTUBE_LINKS_FILE.exists():
        return 1
    
    lines = YOUTUBE_LINKS_FILE.read_text(encoding="utf-8").strip().split("\n")
    if not lines or lines == ['']:
        return 1
    
    # Parse last meeting number
    try:
        last_line = lines[-1].strip()
        if " - " in last_line:
            last_num = int(last_line.split(" - ")[0])
            return last_num + 1
    except (ValueError, IndexError):
        pass
    
    return len(lines) + 1


def append_youtube_link(meeting_number: int, youtube_url: str):
    """Append new meeting link to youtube_links.txt."""
    with open(YOUTUBE_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{meeting_number} - {youtube_url}\n")
    print(f"📝 Link zapisany do: {YOUTUBE_LINKS_FILE}")


def run_full_pipeline(
    audio_path: str,
    meeting_number: int = None,
    date: str = None,
    model: str = "large-v3",
    language: str = "pl",
    device: str = None,
    privacy: str = "unlisted",
) -> dict:
    """
    Run complete meeting processing pipeline.
    
    Steps:
    1. Transcription (audio → text)
    2. Video creation (audio + background → MP4)
    3. YouTube upload
    4. Save link to youtube_links.txt
    """
    audio_path = Path(audio_path)
    date = date or datetime.now().strftime("%Y-%m-%d")
    meeting_number = meeting_number or get_next_meeting_number()
    
    # Output directory
    output_dir = PROJECT_ROOT / "results" / f"meeting_{meeting_number}_{date}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🎬 SKNWPL Full Meeting Pipeline")
    print("=" * 60)
    print(f"📁 Audio: {audio_path}")
    print(f"📅 Date: {date}")
    print(f"#️⃣  Meeting: {meeting_number}")
    print(f"📂 Output: {output_dir}")
    print("=" * 60)
    
    # ===== STEP 1: Transcription =====
    print("\n🎤 STEP 1/4: Transcription")
    print("-" * 40)
    
    # Auto-detect device if not specified
    transcript_kwargs = {
        "model_size": model,
        "language": language,
        "output_dir": str(output_dir),
    }
    if device:
        transcript_kwargs["device"] = device
        if device == "cuda":
            transcript_kwargs["compute_type"] = "float16"
            transcript_kwargs["batch_size"] = 16
    
    result = transcribe_with_faster_whisper(str(audio_path), **transcript_kwargs)
    
    transcript_txt = output_dir / f"{audio_path.stem}_transcript.txt"
    plain_txt = output_dir / f"{audio_path.stem}_plain.txt"
    
    # ===== STEP 2: Create Video =====
    print("\n🎬 STEP 2/4: Creating Video")
    print("-" * 40)
    
    video_path = output_dir / f"{audio_path.stem}.mp4"
    
    create_video_from_audio(
        str(audio_path),
        str(BACKGROUND_IMAGE),
        output_path=str(video_path),
    )
    
    # ===== STEP 3: YouTube Upload =====
    print("\n📤 STEP 3/4: YouTube Upload")
    print("-" * 40)
    
    title = f"Spotkanie SKNWPL #{meeting_number} - {date}"
    description = generate_meeting_description(date)
    
    upload_result = upload_video(
        str(video_path),
        title=title,
        description=description,
        tags=["SKNWPL", "koło naukowe", "spotkanie", "Politechnika Poznańska"],
        privacy_status=privacy,
    )
    
    youtube_url = upload_result["url"]
    
    # ===== STEP 4: Save Link =====
    print("\n💾 STEP 4/4: Saving Link")
    print("-" * 40)
    
    append_youtube_link(meeting_number, youtube_url)
    
    # Also save link in output directory
    link_file = output_dir / "youtube_link.txt"
    link_file.write_text(youtube_url, encoding="utf-8")
    
    # ===== Summary =====
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETED!")
    print("=" * 60)
    print(f"   Meeting: #{meeting_number}")
    print(f"   YouTube: {youtube_url}")
    print(f"   Transcript: {transcript_txt}")
    print(f"   Video: {video_path}")
    print(f"   Links file: {YOUTUBE_LINKS_FILE}")
    print("=" * 60)
    
    return {
        "meeting_number": meeting_number,
        "youtube_url": youtube_url,
        "video_path": str(video_path),
        "transcript_path": str(transcript_txt),
        "output_dir": str(output_dir),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Full Meeting Pipeline - Transcription + Video + YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect everything
  python full_pipeline.py audio/meeting.mkv
  
  # Specify meeting number
  python full_pipeline.py audio/meeting.mkv --meeting-number 42
  
  # Force GPU
  python full_pipeline.py audio/meeting.mkv --device cuda --model large-v3
        """
    )
    
    parser.add_argument("audio", help="Path to audio/video file")
    parser.add_argument("--meeting-number", "-n", type=int, 
                        help="Meeting number (auto-increment if not specified)")
    parser.add_argument("--date", "-d", help="Meeting date (YYYY-MM-DD)")
    parser.add_argument("--model", "-m", default="large-v3",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model (default: large-v3)")
    parser.add_argument("--language", "-l", default="pl", help="Language code")
    parser.add_argument("--device", choices=["cpu", "cuda"],
                        help="Device (auto-detect if not specified)")
    parser.add_argument("--privacy", default="unlisted",
                        choices=["public", "private", "unlisted"],
                        help="YouTube privacy status")
    
    args = parser.parse_args()
    
    run_full_pipeline(
        args.audio,
        meeting_number=args.meeting_number,
        date=args.date,
        model=args.model,
        language=args.language,
        device=args.device,
        privacy=args.privacy,
    )


if __name__ == "__main__":
    main()
