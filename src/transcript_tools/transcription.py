"""
Moduł do transkrypcji audio używając faster-whisper.
Zoptymalizowany dla CPU (laptop bez GPU) z językiem polskim.

Benchmarki (13 min audio, CPU i7-12700K):
- small + int8 + batch_size=8: 51s, 3.6GB RAM
- small + int8: 1m42s, 1.5GB RAM
- small + fp32: 2m37s, 2.3GB RAM
"""

import os
import json
from pathlib import Path
from datetime import timedelta
from typing import Optional, Literal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """Konwertuje sekundy na format HH:MM:SS"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def detect_device() -> tuple[str, str]:
    """
    Wykrywa dostępne urządzenie (GPU/CPU) i zwraca optymalne ustawienia.
    
    Returns:
        (device, compute_type) - np. ("cuda", "float16") lub ("cpu", "int8")
    """
    try:
        import torch
        if torch.cuda.is_available():
            logger.info("🎮 Wykryto GPU CUDA - używam float16")
            return "cuda", "float16"
    except ImportError:
        pass
    
    # CPU - używamy int8 dla szybkości i mniejszego zużycia RAM
    logger.info("💻 Używam CPU z int8 (zoptymalizowane dla laptopa)")
    return "cpu", "int8"


def get_optimal_settings(
    device: str,
    available_ram_gb: Optional[float] = None
) -> dict:
    """
    Zwraca optymalne ustawienia dla danego urządzenia.
    
    Dla CPU z polskim:
    - small model: dobry balans jakości i szybkości
    - int8: 2x szybszy niż fp32, połowa RAM
    - batch_size: zależy od dostępnego RAM
    """
    if device == "cuda":
        return {
            "model_size": "medium",  # Lepszy dla polskiego na GPU
            "compute_type": "float16",
            "batch_size": 8,
            "beam_size": 5,
            "cpu_threads": 4,
        }
    
    # CPU settings
    # Sprawdź dostępny RAM
    try:
        import psutil
        available_ram_gb = psutil.virtual_memory().available / (1024**3)
        logger.info(f"📊 Dostępny RAM: {available_ram_gb:.1f} GB")
    except ImportError:
        available_ram_gb = available_ram_gb or 4.0  # Zakładamy 4GB
    
    if available_ram_gb >= 4.0:
        # Więcej RAM = możemy użyć batch processing (szybsze)
        return {
            "model_size": "small",  # small jest optymalny dla CPU
            "compute_type": "int8",
            "batch_size": 8,  # 51s vs 1m42s dla 13 min audio
            "beam_size": 5,
            "cpu_threads": 0,  # 0 = auto (wszystkie rdzenie)
        }
    else:
        # Mniej RAM = oszczędzamy pamięć
        return {
            "model_size": "small",
            "compute_type": "int8",
            "batch_size": 1,  # Bez batch = mniej RAM
            "beam_size": 5,
            "cpu_threads": 0,
        }


def transcribe_with_faster_whisper(
    audio_path: str,
    model_size: Optional[str] = None,
    language: str = "pl",
    output_dir: Optional[str] = None,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
    batch_size: Optional[int] = None,
) -> dict:
    """
    Transkrybuje audio używając faster-whisper.
    Automatycznie wykrywa CPU/GPU i dostosowuje ustawienia.
    
    Args:
        audio_path: Ścieżka do pliku audio/wideo
        model_size: Rozmiar modelu (tiny, base, small, medium, large-v3)
                   Domyślnie: small dla CPU, medium dla GPU
        language: Kod języka (pl dla polskiego)
        output_dir: Katalog wyjściowy (domyślnie ten sam co audio)
        device: "cpu" lub "cuda" (auto-detect jeśli None)
        compute_type: "int8", "float16", "float32" (auto jeśli None)
        batch_size: Rozmiar batcha (auto jeśli None)
    
    Returns:
        Dict z transkrypcją i metadanymi
    """
    try:
        from faster_whisper import WhisperModel, BatchedInferencePipeline
    except ImportError:
        raise ImportError(
            "Zainstaluj faster-whisper:\n"
            "  pip install faster-whisper\n\n"
            "Wymaga również FFmpeg w systemie:\n"
            "  Windows: winget install ffmpeg"
        )
    
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {audio_path}")
    
    output_dir = Path(output_dir) if output_dir else audio_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-detect urządzenia i ustawień
    detected_device, detected_compute = detect_device()
    device = device or detected_device
    
    # Pobierz optymalne ustawienia
    optimal = get_optimal_settings(device)
    
    model_size = model_size or optimal["model_size"]
    compute_type = compute_type or optimal["compute_type"]
    batch_size = batch_size if batch_size is not None else optimal["batch_size"]
    beam_size = optimal["beam_size"]
    cpu_threads = optimal["cpu_threads"]
    
    print("=" * 60)
    print("🎤 FASTER-WHISPER TRANSKRYPCJA")
    print("=" * 60)
    print(f"📂 Plik: {audio_path.name}")
    print(f"🔧 Urządzenie: {device.upper()}")
    print(f"📦 Model: {model_size}")
    print(f"⚡ Precision: {compute_type}")
    print(f"📊 Batch size: {batch_size}")
    print(f"🌍 Język: {language}")
    print("=" * 60)
    
    print(f"\n📥 Ładowanie modelu {model_size}...")
    print("   (pierwsze uruchomienie pobiera model ~500MB-3GB)")
    
    # Załaduj model
    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads,
    )
    
    print("✅ Model załadowany!\n")
    print("🔄 Transkrybuję... (to może chwilę potrwać)")
    
    # Użyj batched inference jeśli batch_size > 1
    if batch_size > 1:
        # Batched inference - znacznie szybsze
        batched_model = BatchedInferencePipeline(model=model)
        segments, info = batched_model.transcribe(
            str(audio_path),
            language=language,
            batch_size=batch_size,
            beam_size=beam_size,
            vad_filter=True,  # Filtruje ciszę - szybsze
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
        )
    else:
        # Standard inference
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
        )
    
    # Zbierz segmenty
    transcript_segments = []
    full_text_parts = []
    
    print("\n📝 Przetwarzam segmenty...")
    
    for segment in segments:
        seg_data = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "start_formatted": format_timestamp(segment.start),
            "end_formatted": format_timestamp(segment.end),
        }
        transcript_segments.append(seg_data)
        full_text_parts.append(segment.text.strip())
        
        # Pokaż postęp
        print(f"  [{seg_data['start_formatted']}] {segment.text.strip()[:50]}...")
    
    result = {
        "audio_file": str(audio_path),
        "language": language,
        "duration": info.duration,
        "duration_formatted": format_timestamp(info.duration),
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "segments": transcript_segments,
        "full_text": " ".join(full_text_parts),
    }
    
    # Zapisz wyniki
    base_name = audio_path.stem
    
    # JSON z pełnymi danymi
    json_path = output_dir / f"{base_name}_transcript.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON: {json_path}")
    
    # Plik tekstowy z timestampami (format do dokumentacji)
    txt_path = output_dir / f"{base_name}_transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in transcript_segments:
            f.write(f"[[{seg['start_formatted']}]]\n")
            f.write(f"{seg['text']}\n\n")
    print(f"💾 TXT z timestampami: {txt_path}")
    
    # Czysty tekst (do wklejenia do ChatGPT)
    plain_path = output_dir / f"{base_name}_plain.txt"
    with open(plain_path, "w", encoding="utf-8") as f:
        f.write(result["full_text"])
    print(f"💾 Czysty tekst: {plain_path}")
    
    print("\n" + "=" * 60)
    print("✅ TRANSKRYPCJA ZAKOŃCZONA!")
    print("=" * 60)
    print(f"   Długość nagrania: {result['duration_formatted']}")
    print(f"   Segmentów: {len(transcript_segments)}")
    print(f"   Słów: ~{len(result['full_text'].split())}")
    print("=" * 60)
    
    return result


def transcribe_with_openai(
    audio_path: str,
    api_key: Optional[str] = None,
    language: str = "pl",
    output_dir: Optional[str] = None
) -> dict:
    """
    Transkrybuje audio używając OpenAI Whisper API.
    Płatne (~$0.006/minuta) ale nie wymaga lokalnych zasobów.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Zainstaluj openai: pip install openai")
    
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "Podaj API key przez argument lub ustaw OPENAI_API_KEY"
        )
    
    audio_path = Path(audio_path)
    output_dir = Path(output_dir) if output_dir else audio_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    client = OpenAI(api_key=api_key)
    
    print(f"🎤 Wysyłam do OpenAI API: {audio_path.name}")
    
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    transcript_segments = []
    for seg in response.segments:
        seg_data = {
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "start_formatted": format_timestamp(seg.start),
            "end_formatted": format_timestamp(seg.end),
        }
        transcript_segments.append(seg_data)
    
    result = {
        "audio_file": str(audio_path),
        "language": response.language,
        "duration": response.duration,
        "duration_formatted": format_timestamp(response.duration),
        "segments": transcript_segments,
        "full_text": response.text,
    }
    
    base_name = audio_path.stem
    
    json_path = output_dir / f"{base_name}_transcript.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    txt_path = output_dir / f"{base_name}_transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in transcript_segments:
            f.write(f"[[{seg['start_formatted']}]]\n")
            f.write(f"{seg['text']}\n\n")
    
    plain_path = output_dir / f"{base_name}_plain.txt"
    with open(plain_path, "w", encoding="utf-8") as f:
        f.write(result["full_text"])
    
    print(f"✅ Transkrypcja zakończona! Zapisano do {output_dir}")
    
    return result


def transcribe(
    audio_path: str,
    method: str = "local",
    **kwargs
) -> dict:
    """
    Główna funkcja do transkrypcji.
    
    Args:
        audio_path: Ścieżka do pliku audio/wideo
        method: "local" (faster-whisper) lub "openai" (API)
        **kwargs: Dodatkowe argumenty dla wybranej metody
    """
    if method == "local":
        return transcribe_with_faster_whisper(audio_path, **kwargs)
    elif method == "openai":
        return transcribe_with_openai(audio_path, **kwargs)
    else:
        raise ValueError(f"Nieznana metoda: {method}. Użyj 'local' lub 'openai'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transkrypcja audio spotkań (faster-whisper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  # Automatyczne ustawienia (zalecane)
  python transcription.py nagranie.mp3
  
  # Wymuś konkretny model
  python transcription.py nagranie.mp3 --model medium
  
  # OpenAI API (płatne, ale szybkie)
  python transcription.py nagranie.mp3 --method openai --api-key sk-xxx
        """
    )
    parser.add_argument("audio", help="Ścieżka do pliku audio/wideo")
    parser.add_argument("--method", choices=["local", "openai"], default="local",
                        help="Metoda transkrypcji (domyślnie: local)")
    parser.add_argument("--model", 
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Rozmiar modelu (domyślnie: auto)")
    parser.add_argument("--language", default="pl", help="Kod języka")
    parser.add_argument("--output", help="Katalog wyjściowy")
    parser.add_argument("--api-key", help="OpenAI API key (dla --method openai)")
    parser.add_argument("--device", choices=["cpu", "cuda"],
                        help="Urządzenie (domyślnie: auto-detect)")
    parser.add_argument("--batch-size", type=int,
                        help="Batch size (domyślnie: auto)")
    
    args = parser.parse_args()
    
    if args.method == "local":
        transcribe_with_faster_whisper(
            args.audio,
            model_size=args.model,
            language=args.language,
            output_dir=args.output,
            device=args.device,
            batch_size=args.batch_size,
        )
    else:
        transcribe_with_openai(
            args.audio,
            api_key=args.api_key,
            language=args.language,
            output_dir=args.output
        )
