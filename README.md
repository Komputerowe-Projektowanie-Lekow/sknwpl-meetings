# SKNWPL Meetings

System do automatycznego przetwarzania nagrań spotkań koła naukowego.

## 🎯 Funkcje

- **Transkrypcja** - automatyczna zamiana audio na tekst (Whisper)
- **Tworzenie wideo** - łączenie audio z obrazem tła (FFmpeg)
- **Prompty AI** - gotowe prompty do ChatGPT/Gemini
- **Upload YouTube** - automatyczne wgrywanie na kanał



python meeting.py upload ".\last-week-in-sknwpl\week_24_30\2025-11-28 18-05-45.mp4" --title "Spotkanie SKNWPL 2025-11-28"

python meeting.py process "resources/audio/2025-11-28 18-05-45.mkv" --date 2025-11-28

## 🚀 Szybki start

### 1. Instalacja

```bash
# Zainstaluj zależności
pip install -e .

# Zainstaluj FFmpeg (wymagane do wideo)
# Windows:
winget install ffmpeg
# lub pobierz z https://ffmpeg.org/download.html
```

### 2. Przetwórz spotkanie (pełny przepływ)

```bash
python meeting.py process resources/audio/nagranie.mkv --date 2025-11-28
```

To automatycznie:
1. ✅ Transkrybuje audio (Whisper)
2. ✅ Tworzy wideo MP4 z logo
3. ✅ Generuje prompty do ChatGPT/Gemini
4. 📝 Wymaga ręcznego wklejenia promptów do AI

### 3. Wykonaj kroki ręczne

Po automatycznym przetworzeniu:

1. Otwórz `prompt_01_highlights.txt`
2. Skopiuj całość → wklej do ChatGPT lub Gemini
3. Zapisz wynik jako `highlights.md`

4. Otwórz `prompt_02_summary.txt`
5. Skopiuj całość → wklej do ChatGPT lub Gemini
6. Zapisz wynik jako `meeting-transcript.md`

### 4. Upload na YouTube (opcjonalnie)

```bash
python meeting.py upload spotkanie.mp4 --title "Spotkanie SKNWPL 2025-11-28"
```

## 📁 Struktura projektu

```
sknwpl-meetings/
├── meeting.py              # Główny skrypt
├── resources/
│   ├── audio/              # Nagrania audio
│   └── templates/
│       ├── pmarlo_background.png  # Tło do wideo
│       └── prompts.md      # Dokumentacja promptów
├── src/
│   ├── transcript_tools/
│   │   ├── transcription.py      # Transkrypcja Whisper
│   │   ├── audio_to_video.py     # Tworzenie wideo
│   │   └── upload_youtube.py     # Upload YouTube
│   └── llm/
│       └── prompt_manager.py     # Generator promptów
├── last-week-in-sknwpl/    # Wyjście - foldery spotkań
│   └── week_DD_DD/
│       ├── *_transcript.txt      # Transkrypt
│       ├── *.mp4                 # Wideo
│       ├── prompt_*.txt          # Prompty do AI
│       ├── highlights.md         # (ręcznie z ChatGPT)
│       └── meeting-transcript.md # (ręcznie z ChatGPT)
└── credentials/            # YouTube API (gitignore'd)
```

## 🛠️ Komendy

### Pełny przepływ (zalecane)

```bash
python meeting.py process <audio> [opcje]

# Przykład:
python meeting.py process nagranie.mp3 --date 2025-11-28 --notes agenda.txt
```

### Pojedyncze kroki

```bash
# Tylko transkrypcja
python meeting.py transcribe nagranie.mp3

# Tylko wideo
python meeting.py video nagranie.mp3 --background logo.png

# Tylko prompty
python meeting.py prompts transkrypt.txt --notes agenda.txt

# Tylko upload
python meeting.py upload video.mp4 --title "Tytuł" --privacy unlisted
```

## ⚙️ Konfiguracja YouTube API

Aby używać automatycznego uploadu:

1. Idź do [Google Cloud Console](https://console.cloud.google.com/)
2. Stwórz nowy projekt
3. Włącz **YouTube Data API v3**
4. Przejdź do **Credentials** → **Create Credentials** → **OAuth client ID**
5. Wybierz **Desktop app**
6. Pobierz JSON i zapisz jako `credentials/client_secrets.json`
7. Przy pierwszym uruchomieniu zaloguj się przez przeglądarkę

## 💡 Wskazówki

### Automatyczne ustawienia (CPU vs GPU)

System automatycznie wykrywa czy masz GPU i dostosowuje ustawienia:

**CPU (laptop bez GPU):**
- Model: `small` (optymalny dla CPU)
- Precision: `int8` (2x szybszy, połowa RAM)
- Batch: 8 (jeśli masz ≥4GB RAM)

**GPU (CUDA):**
- Model: `medium` (lepszy dla polskiego)
- Precision: `float16`
- Batch: 8

### Benchmarki (13 min audio)

| Konfiguracja | Czas | RAM |
|--------------|------|-----|
| CPU + small + int8 + batch=8 | **51s** | 3.6GB |
| CPU + small + int8 | 1m42s | 1.5GB |
| GPU + medium + fp16 + batch=8 | **17s** | 6GB VRAM |

### Wymuszenie modelu

```bash
# Użyj medium (lepszy dla polskiego, ale wolniejszy na CPU)
python meeting.py process nagranie.mp3 --model medium

# Użyj tiny (najszybszy, ale gorsza jakość)
python meeting.py process nagranie.mp3 --model tiny
```

### Modele Whisper

| Model | RAM (int8) | Jakość PL | Dla CPU |
|-------|------------|-----------|---------|
| tiny | ~1GB | ⭐ | ✅ szybki |
| base | ~1GB | ⭐⭐ | ✅ szybki |
| small | ~1.5GB | ⭐⭐⭐ | ✅ **zalecany** |
| medium | ~3GB | ⭐⭐⭐⭐ | ⚠️ wolny |
| large-v3 | ~6GB | ⭐⭐⭐⭐⭐ | ❌ za wolny |

### ChatGPT vs Gemini

- **ChatGPT Plus**: lepszy w formatowaniu, działa na długich tekstach
- **Gemini Pro**: darmowy, bardzo długi kontekst (do 1M tokenów)

### Bez GPU

faster-whisper działa na CPU, ale wolniej. Dla nagrań >30 min rozważ:
- OpenAI Whisper API (`--method openai`)
- Mniejszy model (`--model small` lub `base`)

## 📝 Format wyjściowy

Inspirowany [tinycorp-meetings](https://github.com/geohotstan/tinycorp-meetings), ale bez podziału na osoby:

```markdown
# 2025-11-28 Spotkanie SKNWPL

### Agenda Spotkania

- Punkt 1
- Punkt 2
- Punkt 3

### Audio

[YouTube Link](https://youtube.com/...)

### Highlights

- **Tytuł 1**: Krótki opis najważniejszego ustalenia.
- **Tytuł 2**: Kolejny ważny punkt.

### Transkrypt

[[00:00:00]]
Tekst wypowiedzi...

[[00:05:30]]
Kolejna część rozmowy...
```

## 🔧 Wymagania

- Python 3.9+
- FFmpeg (do tworzenia wideo)
- ~2-5 GB RAM (dla modelu Whisper)
- Konto ChatGPT Plus lub Gemini Pro (do generowania podsumowań)

## 📄 Licencja

MIT

