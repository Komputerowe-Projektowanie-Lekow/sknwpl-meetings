"""
Manager promptów do generowania podsumowań spotkań.
Generuje gotowe prompty z danymi do wklejenia do ChatGPT/Gemini.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime


PROMPTS_DIR = Path(__file__).parent.parent.parent / "resources" / "templates"


def load_prompt_template(name: str) -> str:
    """Wczytuje szablon promptu z pliku."""
    prompt_file = PROMPTS_DIR / f"{name}.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Nie znaleziono szablonu: {prompt_file}")


def generate_highlights_prompt(transcript: str) -> str:
    """
    Generuje prompt do wygenerowania highlights.
    Skopiuj wynik i wklej do ChatGPT/Gemini.
    """
    return f'''Jesteś asystentem do streszczania spotkań koła naukowego.

Otrzymasz transkrypt spotkania w języku polskim. Twoim zadaniem jest:

1. Przeczytać całość uważnie
2. Wybrać 3-5 NAJWAŻNIEJSZYCH punktów/decyzji/ustaleń
3. Dla każdego punktu napisać:
   - Krótki tytuł (max 10 słów)
   - 1-2 zdania wyjaśnienia

Format wyjściowy (użyj tego dokładnie):

### Highlights

- **[Tytuł punktu 1]**: [1-2 zdania opisu co zostało ustalone/omówione]
- **[Tytuł punktu 2]**: [1-2 zdania opisu]
- **[Tytuł punktu 3]**: [1-2 zdania opisu]

### Tytuł spotkania (propozycja)
[Zaproponuj krótki, opisowy tytuł dla tego spotkania - max 10 słów]

---
TRANSKRYPT SPOTKANIA:

{transcript}'''


def generate_agenda_prompt(notes: str) -> str:
    """
    Generuje prompt do sformatowania agendy z notatek.
    """
    return f'''Jesteś asystentem do formatowania notatek ze spotkań koła naukowego.

Otrzymasz surowe notatki ze spotkania. Twoim zadaniem jest:
1. Wyodrębnić główne punkty agendy
2. Sformatować je w przejrzystą listę
3. Dodać krótkie opisy gdzie to możliwe

Format wyjściowy:

### Agenda Spotkania

- [Punkt 1]: [krótki opis]
- [Punkt 2]: [krótki opis]
- [Punkt 3]: [krótki opis]

---
NOTATKI DO PRZETWORZENIA:

{notes}'''


def generate_full_summary_prompt(
    transcript: str,
    notes: Optional[str] = None,
    date: Optional[str] = None
) -> str:
    """
    Generuje prompt do pełnego podsumowania spotkania.
    """
    date = date or datetime.now().strftime("%Y-%m-%d")
    notes_section = notes if notes else "BRAK"
    
    return f'''Jesteś asystentem do tworzenia dokumentacji spotkań koła naukowego SKNWPL.

Otrzymasz transkrypt ze spotkania i opcjonalnie notatki.
Wygeneruj pełny dokument w formacie Markdown.

FORMAT WYJŚCIOWY (użyj DOKŁADNIE):

# {date} Spotkanie SKNWPL

### Agenda Spotkania

- [punkt 1]
- [punkt 2]
- [punkt 3]

### Audio

[Link zostanie dodany później]

### Highlights

- **[Tytuł 1]**: [Krótki opis - 1-2 zdania]
- **[Tytuł 2]**: [Krótki opis]
- **[Tytuł 3]**: [Krótki opis]

### Transkrypt

[Sformatowany transkrypt z timestampami w formacie [[HH:MM:SS]]]

---
NOTATKI/AGENDA:

{notes_section}

TRANSKRYPT:

{transcript}'''


def generate_youtube_metadata_prompt(
    date: str,
    highlights: str,
    main_topic: str = "różne tematy"
) -> str:
    """
    Generuje prompt do stworzenia tytułu i opisu na YouTube.
    """
    return f'''Jesteś asystentem do tworzenia opisów wideo na YouTube.

Wygeneruj metadane dla wideo ze spotkania koła naukowego:

1. Tytuł wideo (max 60 znaków, po polsku)
2. Opis wideo (z emoji, formatowaniem YouTube)
3. Tagi (5-10 słów kluczowych, po polsku)

FORMAT WYJŚCIOWY:

### Tytuł
[Tytuł wideo]

### Opis
[Opis ze spotkania, emoji, struktura]

### Tagi
tag1, tag2, tag3, tag4, tag5

---
INFORMACJE O SPOTKANIU:

Data: {date}
Temat główny: {main_topic}
Highlights:
{highlights}'''


def generate_transcript_cleanup_prompt(raw_transcript: str) -> str:
    """
    Generuje prompt do poprawienia i sformatowania transkryptu.
    """
    return f'''Jesteś asystentem do formatowania transkryptów spotkań.

Otrzymasz surowy transkrypt z automatycznej transkrypcji.
Twoim zadaniem jest:

1. Poprawić oczywiste błędy transkrypcji
2. Dodać interpunkcję gdzie brakuje
3. Podzielić na logiczne akapity (co ~2-3 minuty lub przy zmianie tematu)
4. Zachować timestampy w formacie [[HH:MM:SS]]

NIE ZMIENIAJ sensu wypowiedzi, kolejności ani timestampów.

Format wyjściowy:

[[00:00:00]]
[Tekst pierwszego fragmentu, poprawiony]

[[00:02:30]]
[Tekst kolejnego fragmentu]

---
TRANSKRYPT DO PRZETWORZENIA:

{raw_transcript}'''


def save_prompt_to_file(prompt: str, output_path: str) -> str:
    """
    Zapisuje prompt do pliku .txt gotowego do skopiowania.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_path.write_text(prompt, encoding="utf-8")
    print(f"💾 Prompt zapisany: {output_path}")
    print(f"   Skopiuj zawartość i wklej do ChatGPT/Gemini")
    
    return str(output_path)


def copy_to_clipboard(text: str) -> bool:
    """
    Kopiuje tekst do schowka (Windows/Mac/Linux).
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        print("📋 Skopiowano do schowka!")
        return True
    except ImportError:
        print("⚠️  Zainstaluj pyperclip: pip install pyperclip")
        return False
    except Exception as e:
        print(f"⚠️  Nie udało się skopiować: {e}")
        return False


if __name__ == "__main__":
    # Przykład użycia
    sample_transcript = """
    [00:00:00] Witam wszystkich na dzisiejszym spotkaniu.
    [00:00:15] Dzisiaj omówimy plany na następny tydzień.
    [00:01:30] Pierwsza rzecz to projekt badawczy.
    """
    
    prompt = generate_highlights_prompt(sample_transcript)
    print("=" * 50)
    print("PROMPT DO WKLEJENIA W CHATGPT:")
    print("=" * 50)
    print(prompt)

