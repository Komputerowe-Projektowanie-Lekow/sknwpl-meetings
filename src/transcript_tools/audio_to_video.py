"""
Moduł do tworzenia wideo z audio i statycznego obrazu tła.
Używa FFmpeg do konwersji.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def check_ffmpeg() -> bool:
    """Sprawdza czy FFmpeg jest zainstalowany."""
    return shutil.which("ffmpeg") is not None


def get_audio_duration(audio_path: str) -> float:
    """Pobiera długość pliku audio w sekundach."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_video_from_audio(
    audio_path: str,
    background_image: str,
    output_path: Optional[str] = None,
    resolution: str = "1920x1080",
    fps: int = 30,
    audio_bitrate: str = "192k",
    video_bitrate: str = "1M",
) -> str:
    """
    Tworzy wideo MP4 z pliku audio i statycznego obrazu tła.
    
    Args:
        audio_path: Ścieżka do pliku audio (mp3, wav, mkv, etc.)
        background_image: Ścieżka do obrazu tła (png, jpg)
        output_path: Ścieżka wyjściowa (domyślnie: audio_path z .mp4)
        resolution: Rozdzielczość wideo (domyślnie 1920x1080)
        fps: Klatki na sekundę
        audio_bitrate: Bitrate audio
        video_bitrate: Bitrate wideo
    
    Returns:
        Ścieżka do utworzonego pliku wideo
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "FFmpeg nie jest zainstalowany!\n"
            "Windows: winget install ffmpeg\n"
            "lub pobierz z https://ffmpeg.org/download.html"
        )
    
    audio_path = Path(audio_path)
    background_image = Path(background_image)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku audio: {audio_path}")
    if not background_image.exists():
        raise FileNotFoundError(f"Nie znaleziono obrazu tła: {background_image}")
    
    # Domyślna ścieżka wyjściowa
    if output_path is None:
        output_path = audio_path.with_suffix(".mp4")
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    width, height = resolution.split("x")
    
    print(f"🎬 Tworzenie wideo...")
    print(f"   Audio: {audio_path.name}")
    print(f"   Tło: {background_image.name}")
    print(f"   Rozdzielczość: {resolution}")
    
    # FFmpeg command:
    # -loop 1: zapętla obraz
    # -i image: wejście obrazu
    # -i audio: wejście audio
    # -c:v libx264: kodek wideo H.264
    # -tune stillimage: optymalizacja dla statycznego obrazu
    # -c:a aac: kodek audio AAC
    # -shortest: kończy gdy skończy się krótszy strumień (audio)
    # -pix_fmt yuv420p: format pikseli kompatybilny z większością graczy
    
    cmd = [
        "ffmpeg",
        "-y",  # Nadpisz bez pytania
        "-loop", "1",
        "-i", str(background_image),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-b:v", video_bitrate,
        "-r", str(fps),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",  # Optymalizacja dla streamingu
        str(output_path)
    ]
    
    print(f"   Uruchamiam FFmpeg...")
    
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    for line in process.stderr:
        if "time=" in line or "frame=" in line:
            print(f"\r   {line.strip()}", end="", flush=True)

    process.wait()
    print()  # Nowa linia po zakończonym wypisywaniu

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg zakończył się błędem: {process.returncode}")
    
    # Pobierz informacje o utworzonym pliku
    duration = get_audio_duration(str(output_path))
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"✅ Wideo utworzone!")
    print(f"   Plik: {output_path}")
    print(f"   Długość: {int(duration // 60)}:{int(duration % 60):02d}")
    print(f"   Rozmiar: {file_size:.1f} MB")
    
    return str(output_path)


def extract_audio_from_video(
    video_path: str,
    output_path: Optional[str] = None,
    format: str = "mp3"
) -> str:
    """
    Wyodrębnia audio z pliku wideo.
    
    Args:
        video_path: Ścieżka do pliku wideo
        output_path: Ścieżka wyjściowa
        format: Format audio (mp3, wav, aac)
    
    Returns:
        Ścieżka do pliku audio
    """
    if not check_ffmpeg():
        raise RuntimeError("FFmpeg nie jest zainstalowany!")
    
    video_path = Path(video_path)
    
    if output_path is None:
        output_path = video_path.with_suffix(f".{format}")
    else:
        output_path = Path(output_path)
    
    print(f"🎵 Wyodrębniam audio z {video_path.name}...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",  # Bez wideo
        "-acodec", "libmp3lame" if format == "mp3" else "copy",
        "-q:a", "2",  # Jakość
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    
    print(f"✅ Audio zapisane: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tworzenie wideo z audio i obrazu tła")
    parser.add_argument("audio", help="Ścieżka do pliku audio")
    parser.add_argument("--background", "-b", required=True,
                        help="Ścieżka do obrazu tła")
    parser.add_argument("--output", "-o", help="Ścieżka wyjściowa")
    parser.add_argument("--resolution", "-r", default="1920x1080",
                        help="Rozdzielczość wideo (domyślnie: 1920x1080)")
    
    args = parser.parse_args()
    
    create_video_from_audio(
        args.audio,
        args.background,
        output_path=args.output,
        resolution=args.resolution
    )

