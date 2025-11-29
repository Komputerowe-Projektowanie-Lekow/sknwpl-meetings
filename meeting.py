#!/usr/bin/env python3
"""
SKNWPL Meeting Processor
========================

Główny skrypt do przetwarzania spotkań koła naukowego.

Przepływ pracy:
1. Transkrypcja audio → tekst
2. Tworzenie wideo (audio + tło)
3. Generowanie promptów do ChatGPT/Gemini
4. Upload na YouTube

Użycie:
    python meeting.py process <audio_file> [--date 2025-11-28] [--notes notatki.txt]
    python meeting.py transcribe <audio_file>
    python meeting.py video <audio_file>
    python meeting.py prompts <transcript_file>
    python meeting.py upload <video_file> --title "Tytuł"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

# Dodaj src do path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from transcript_tools.transcription import transcribe
from transcript_tools.audio_to_video import create_video_from_audio
from transcript_tools.upload_youtube import upload_video, generate_meeting_description
from llm.prompt_manager import (
    generate_highlights_prompt,
    generate_full_summary_prompt,
    generate_youtube_metadata_prompt,
    save_prompt_to_file,
    copy_to_clipboard,
)


# Domyślne ścieżki
PROJECT_ROOT = Path(__file__).parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
TEMPLATES_DIR = RESOURCES_DIR / "templates"
OUTPUT_DIR = PROJECT_ROOT / "last-week-in-sknwpl"
DEFAULT_BACKGROUND = TEMPLATES_DIR / "pmarlo_background.png"


@contextmanager
def log_to_file(log_path: Path):
    """Kieruje stdout/stderr rownoczesnie do konsoli i pliku."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")

    class Tee:
        def __init__(self, original, file):
            self.original = original
            self.file = file

        def write(self, data):
            self.original.write(data)
            self.file.write(data)

        def flush(self):
            self.original.flush()
            self.file.flush()

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = Tee(sys.stdout, log_file), Tee(sys.stderr, log_file)
    try:
        yield log_path
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        log_file.flush()
        sys.stdout, sys.stderr = old_stdout, old_stderr
        log_file.close()


def get_week_folder(date: Optional[str] = None) -> Path:
    """Generuje ścieżkę do folderu tygodnia."""
    if date:
        dt = datetime.strptime(date, "%Y-%m-%d")
    else:
        dt = datetime.now()
    
    # Format: week_DD_DD (początek i koniec tygodnia)
    week_start = dt - timedelta(days=dt.weekday())
    week_end = week_start + timedelta(days=6)
    
    folder_name = f"week_{week_start.day:02d}_{week_end.day:02d}"
    return OUTPUT_DIR / folder_name


from datetime import timedelta


def cmd_transcribe(args):
    """Komenda: transkrypcja audio."""
    audio_path = Path(args.audio)
    output_dir = args.output or get_week_folder(args.date)
    
    print(f"🎤 Rozpoczynam transkrypcję: {audio_path.name}")
    print(f"📁 Output: {output_dir}")
    
    result = transcribe(
        str(audio_path),
        method=args.method,
        model_size=args.model,
        language=args.language,
        output_dir=str(output_dir),
    )
    
    # Wygeneruj prompt do highlights
    print("\n" + "=" * 50)
    print("📝 NASTĘPNY KROK: Wygeneruj highlights")
    print("=" * 50)
    
    transcript_txt = output_dir / f"{audio_path.stem}_transcript.txt"
    if transcript_txt.exists():
        transcript = transcript_txt.read_text(encoding="utf-8")
        prompt = generate_highlights_prompt(transcript)
        prompt_file = output_dir / "prompt_highlights.txt"
        save_prompt_to_file(prompt, str(prompt_file))
        print(f"\n1. Otwórz plik: {prompt_file}")
        print("2. Skopiuj całą zawartość")
        print("3. Wklej do ChatGPT lub Gemini")
        print("4. Zapisz wynik do pliku highlights.md")
    
    return result


def cmd_video(args):
    """Komenda: tworzenie wideo z audio."""
    audio_path = Path(args.audio)
    background = Path(args.background) if args.background else DEFAULT_BACKGROUND
    output_dir = args.output or get_week_folder(args.date)
    output_path = Path(output_dir) / f"{audio_path.stem}.mp4"
    
    print(f"🎬 Tworzenie wideo...")
    
    video_path = create_video_from_audio(
        str(audio_path),
        str(background),
        output_path=str(output_path),
        resolution=args.resolution,
    )
    
    print(f"\n✅ Wideo gotowe: {video_path}")
    return video_path


def cmd_prompts(args):
    """Komenda: generowanie promptów."""
    transcript_path = Path(args.transcript)
    output_dir = transcript_path.parent
    
    transcript = transcript_path.read_text(encoding="utf-8")
    
    # Wczytaj notatki jeśli podane
    notes = None
    if args.notes:
        notes_path = Path(args.notes)
        if notes_path.exists():
            notes = notes_path.read_text(encoding="utf-8")
    
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    
    prompts_to_generate = []
    
    if args.type in ["all", "highlights"]:
        prompts_to_generate.append((
            "highlights",
            generate_highlights_prompt(transcript)
        ))
    
    if args.type in ["all", "summary"]:
        prompts_to_generate.append((
            "summary",
            generate_full_summary_prompt(transcript, notes, date)
        ))
    
    print(f"📝 Generuję prompty...")
    
    for name, prompt in prompts_to_generate:
        prompt_file = output_dir / f"prompt_{name}.txt"
        save_prompt_to_file(prompt, str(prompt_file))
    
    if args.clipboard and prompts_to_generate:
        # Kopiuj pierwszy prompt do schowka
        copy_to_clipboard(prompts_to_generate[0][1])
    
    print("\n📋 INSTRUKCJA:")
    print("1. Otwórz wygenerowany plik prompt_*.txt")
    print("2. Skopiuj całą zawartość")
    print("3. Wklej do ChatGPT lub Gemini")
    print("4. Zapisz wynik w tym samym katalogu")


def cmd_upload(args):
    """Komenda: upload na YouTube."""
    video_path = Path(args.video)
    
    # Wczytaj highlights jeśli istnieją
    highlights_path = video_path.parent / "highlights.md"
    highlights = ""
    if highlights_path.exists():
        highlights = highlights_path.read_text(encoding="utf-8")
    
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    description = generate_meeting_description(date, highlights=highlights)
    
    result = upload_video(
        str(video_path),
        title=args.title or f"Spotkanie SKNWPL {date}",
        description=args.description or description,
        tags=args.tags or ["SKNWPL", "koło naukowe", "spotkanie"],
        privacy_status=args.privacy,
    )
    
    # Zapisz link do pliku
    link_file = video_path.parent / "youtube_link.txt"
    link_file.write_text(result["url"], encoding="utf-8")
    print(f"💾 Link zapisany: {link_file}")
    
    return result


def cmd_process(args):
    """
    Komenda: pelny przeplyw pracy.
    Wykonuje wszystkie kroki automatycznie.
    """
    audio_path = Path(args.audio)
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    output_dir = get_week_folder(date)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / f"{audio_path.stem}_log.txt"

    with log_to_file(log_file):
        print("=" * 60)
        print("?? SKNWPL Meeting Processor")
        print("=" * 60)
        print(f"?? Audio: {audio_path}")
        print(f"?? Data: {date}")
        print(f"?? Output: {output_dir}")
        print("=" * 60)
        
        # Krok 1: Transkrypcja
        print("\n?? KROK 1/4: Transkrypcja audio")
        print("-" * 40)
        
        result = transcribe(
            str(audio_path),
            method="local",
            model_size=args.model,
            language="pl",
            output_dir=str(output_dir),
        )
        
        transcript_txt = output_dir / f"{audio_path.stem}_transcript.txt"
        transcript = transcript_txt.read_text(encoding="utf-8")
        
        # Krok 2: Tworzenie wideo
        print("\n?? KROK 2/4: Tworzenie wideo")
        print("-" * 40)
        
        background = Path(args.background) if args.background else DEFAULT_BACKGROUND
        video_path = output_dir / f"{audio_path.stem}.mp4"
        
        create_video_from_audio(
            str(audio_path),
            str(background),
            output_path=str(video_path),
        )
        
        # Krok 3: Generowanie promptów
        print("\n?? KROK 3/4: Generowanie promptów do ChatGPT/Gemini")
        print("-" * 40)
        
        # Wczytaj notatki jesli podane
        notes = None
        if args.notes:
            notes_path = Path(args.notes)
            if notes_path.exists():
                notes = notes_path.read_text(encoding="utf-8")
                print(f"?? Wczytano notatki: {notes_path}")
        
        # Prompt do highlights
        highlights_prompt = generate_highlights_prompt(transcript)
        highlights_prompt_file = output_dir / "prompt_01_highlights.txt"
        save_prompt_to_file(highlights_prompt, str(highlights_prompt_file))
        
        # Prompt do pelnego podsumowania
        summary_prompt = generate_full_summary_prompt(transcript, notes, date)
        summary_prompt_file = output_dir / "prompt_02_summary.txt"
        save_prompt_to_file(summary_prompt, str(summary_prompt_file))
        
        # Krok 4: Instrukcje koncowe
        print("\n?? KROK 4/4: Instrukcje manualne")
        print("-" * 40)
        
        print("""
��������������������������������������������������������������ͻ
�  POZOSTALE KROKI DO WYKONANIA RECZNIE:                      �
��������������������������������������������������������������͹
�                                                              �
�  1??  HIGHLIGHTS:                                             �
�       Otwórz: prompt_01_highlights.txt                      �
�       Skopiuj calosc do ChatGPT/Gemini                      �
�       Zapisz wynik jako: highlights.md                      �
�                                                              �
�  2??  PELNE PODSUMOWANIE:                                     �
�       Otwórz: prompt_02_summary.txt                         �
�       Skopiuj calosc do ChatGPT/Gemini                      �
�       Zapisz wynik jako: meeting-transcript.md              �
�                                                              �
�  3??  UPLOAD NA YOUTUBE (opcjonalnie):                        �
�      python meeting.py upload <video.mp4> --title "Tytul"    �
�                                                              �
��������������������������������������������������������������ͼ
""")
        
        print(f"\n?? Wszystkie pliki w: {output_dir}")
        print("\n? Automatyczne przetwarzanie zakonczone!")
        print(f"\n💾 Log zapisany: {log_file}")
        
        # Zapisz podsumowanie
        summary_file = output_dir / "README.md"
        summary_file.write_text(f"""# Spotkanie {date}

## Pliki

- `{audio_path.stem}_transcript.txt` - transkrypt z timestampami
- `{audio_path.stem}_plain.txt` - czysty tekst do ChatGPT
- `{audio_path.stem}.mp4` - wideo do YouTube

## Prompty

- `prompt_01_highlights.txt` - wklej do ChatGPT  zapisz jako `highlights.md`
- `prompt_02_summary.txt` - wklej do ChatGPT  zapisz jako `meeting-transcript.md`

## Status

- [x] Transkrypcja
- [x] Wideo
- [ ] Highlights (recznie przez ChatGPT)
- [ ] Podsumowanie (recznie przez ChatGPT)  
- [ ] Upload YouTube
""", encoding="utf-8")

    # Info dla wywolujacego
    print(f"\n(plik logu: {log_file})")

def main():
    parser = argparse.ArgumentParser(
        description="SKNWPL Meeting Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:

  # Pełny przepływ pracy (zalecane):
  python meeting.py process nagranie.mp3 --date 2025-11-28

  # Tylko transkrypcja:
  python meeting.py transcribe nagranie.mp3

  # Tylko tworzenie wideo:
  python meeting.py video nagranie.mp3 --background logo.png

  # Upload na YouTube:
  python meeting.py upload spotkanie.mp4 --title "Spotkanie 2025-11-28"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Dostępne komendy")
    
    # Komenda: process (pełny przepływ)
    p_process = subparsers.add_parser("process", help="Pełny przepływ pracy")
    p_process.add_argument("audio", help="Plik audio/wideo")
    p_process.add_argument("--date", "-d", help="Data spotkania (YYYY-MM-DD)")
    p_process.add_argument("--notes", "-n", help="Plik z notatkami/agendą")
    p_process.add_argument("--background", "-b", help="Obraz tła do wideo")
    p_process.add_argument("--model", default=None,
                          help="Model Whisper (auto/tiny/base/small/medium/large-v3)")
    p_process.set_defaults(func=cmd_process)
    
    # Komenda: transcribe
    p_transcribe = subparsers.add_parser("transcribe", help="Transkrypcja audio")
    p_transcribe.add_argument("audio", help="Plik audio/wideo")
    p_transcribe.add_argument("--method", choices=["local", "openai"], default="local")
    p_transcribe.add_argument("--model", default=None,
                              help="Model Whisper (domyślnie: auto)")
    p_transcribe.add_argument("--language", default="pl")
    p_transcribe.add_argument("--output", "-o", help="Katalog wyjściowy")
    p_transcribe.add_argument("--date", "-d", help="Data spotkania")
    p_transcribe.set_defaults(func=cmd_transcribe)
    
    # Komenda: video
    p_video = subparsers.add_parser("video", help="Tworzenie wideo z audio")
    p_video.add_argument("audio", help="Plik audio")
    p_video.add_argument("--background", "-b", help="Obraz tła")
    p_video.add_argument("--output", "-o", help="Katalog wyjściowy")
    p_video.add_argument("--resolution", "-r", default="1920x1080")
    p_video.add_argument("--date", "-d", help="Data spotkania")
    p_video.set_defaults(func=cmd_video)
    
    # Komenda: prompts
    p_prompts = subparsers.add_parser("prompts", help="Generowanie promptów")
    p_prompts.add_argument("transcript", help="Plik z transkryptem")
    p_prompts.add_argument("--notes", "-n", help="Plik z notatkami")
    p_prompts.add_argument("--date", "-d", help="Data spotkania")
    p_prompts.add_argument("--type", choices=["all", "highlights", "summary"],
                          default="all", help="Typ promptu")
    p_prompts.add_argument("--clipboard", "-c", action="store_true",
                          help="Kopiuj do schowka")
    p_prompts.set_defaults(func=cmd_prompts)
    
    # Komenda: upload
    p_upload = subparsers.add_parser("upload", help="Upload na YouTube")
    p_upload.add_argument("video", help="Plik wideo")
    p_upload.add_argument("--title", "-t", help="Tytuł wideo")
    p_upload.add_argument("--description", help="Opis wideo")
    p_upload.add_argument("--tags", nargs="+", help="Tagi")
    p_upload.add_argument("--privacy", choices=["public", "private", "unlisted"],
                         default="unlisted")
    p_upload.add_argument("--date", "-d", help="Data spotkania")
    p_upload.set_defaults(func=cmd_upload)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()

