# Prompty do ChatGPT / Gemini dla Spotkań SKNWPL

Poniższe prompty służą do automatycznego generowania podsumowań, agendy i highlights ze spotkań.
Skopiuj odpowiedni prompt i wklej wraz z transkryptem do ChatGPT lub Gemini.

---

## 1. 📝 GENEROWANIE AGENDY Z NOTATEK

Użyj tego promptu gdy masz swoje notatki/agendę ze spotkania i chcesz je sformatować.

```
Jesteś asystentem do formatowania notatek ze spotkań koła naukowego.

Otrzymasz surowe notatki ze spotkania. Twoim zadaniem jest:
1. Wyodrębnić główne punkty agendy
2. Sformatować je w przejrzystą listę
3. Dodać krótkie opisy gdzie to możliwe

Format wyjściowy (użyj tego dokładnie):

### Agenda Spotkania

**Data:** [data ze spotkania]
**Czas:** [czas jeśli podany]

- [Punkt 1]: [krótki opis]
- [Punkt 2]: [krótki opis]
- [Punkt 3]: [krótki opis]
...

---
NOTATKI DO PRZETWORZENIA:

[WKLEJ TUTAJ SWOJE NOTATKI]
```

---

## 2. 🎯 GENEROWANIE HIGHLIGHTS (STRESZCZENIA)

Użyj po transkrypcji, aby wygenerować najważniejsze punkty.

```
Jesteś asystentem do streszczania spotkań koła naukowego.

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
...

### Tytuł spotkania (propozycja)
[Zaproponuj krótki, opisowy tytuł dla tego spotkania - max 10 słów]

---
TRANSKRYPT SPOTKANIA:

[WKLEJ TUTAJ TRANSKRYPT]
```

---

## 3. 📋 PEŁNE PODSUMOWANIE SPOTKANIA

Użyj do stworzenia kompletnego dokumentu markdown ze spotkania.

```
Jesteś asystentem do tworzenia dokumentacji spotkań koła naukowego SKNWPL.

Otrzymasz:
1. Transkrypt ze spotkania
2. (Opcjonalnie) Notatki/agendę przygotowaną przed spotkaniem

Twoim zadaniem jest wygenerować pełny dokument w formacie Markdown.

FORMAT WYJŚCIOWY (użyj tego DOKŁADNIE):

# [DATA] Spotkanie SKNWPL

### Agenda Spotkania

- [punkt 1]
- [punkt 2]
- [punkt 3]
...

### Audio

[Link zostanie dodany później]

### Highlights

- **[Tytuł 1]**: [Krótki opis najważniejszego punktu - 1-2 zdania]
- **[Tytuł 2]**: [Krótki opis]
- **[Tytuł 3]**: [Krótki opis]

### Transkrypt

[TUTAJ WKLEJ PRZETWORONY TRANSKRYPT Z TIMESTAMPAMI]

---
DANE WEJŚCIOWE:

NOTATKI/AGENDA (jeśli są):
[WKLEJ TUTAJ NOTATKI LUB NAPISZ "BRAK"]

TRANSKRYPT:
[WKLEJ TUTAJ TRANSKRYPT]
```

---

## 4. 🔄 FORMATOWANIE TRANSKRYPTU

Użyj do poprawienia i sformatowania surowego transkryptu.

```
Jesteś asystentem do formatowania transkryptów spotkań.

Otrzymasz surowy transkrypt z automatycznej transkrypcji (Whisper).
Twoim zadaniem jest:

1. Poprawić oczywiste błędy transkrypcji
2. Dodać interpunkcję gdzie brakuje
3. Podzielić na logiczne akapity (co ~2-3 minuty lub przy zmianie tematu)
4. Zachować timestampy w formacie [[HH:MM:SS]]

NIE ZMIENIAJ:
- Sensu wypowiedzi
- Kolejności
- Timestampów (tylko przepisz je poprawnie)

Format wyjściowy:

[[00:00:00]]
[Tekst pierwszego fragmentu, poprawiony i z interpunkcją]

[[00:02:30]]
[Tekst kolejnego fragmentu]

...

---
TRANSKRYPT DO PRZETWORZENIA:

[WKLEJ TUTAJ SUROWY TRANSKRYPT]
```

---

## 5. 🎬 GENEROWANIE TYTUŁU I OPISU NA YOUTUBE

Użyj do stworzenia metadanych dla wideo na YouTube.

```
Jesteś asystentem do tworzenia opisów wideo na YouTube.

Otrzymasz informacje o spotkaniu koła naukowego. Wygeneruj:

1. Tytuł wideo (max 60 znaków)
2. Opis wideo (z formatowaniem YouTube)
3. Tagi (5-10 słów kluczowych)

FORMAT WYJŚCIOWY:

### Tytuł
[Tytuł wideo]

### Opis
[Opis z emoji, timestampami najważniejszych momentów jeśli są podane, i linkami]

### Tagi
tag1, tag2, tag3, tag4, tag5

---
INFORMACJE O SPOTKANIU:

Data: [WPISZ DATĘ]
Temat główny: [WPISZ TEMAT LUB "różne tematy"]
Highlights:
[WKLEJ HIGHLIGHTS LUB KRÓTKI OPIS]
```

---

## 💡 WSKAZÓWKI

1. **ChatGPT Plus** - możesz wrzucić plik audio bezpośrednio (Advanced Voice) lub użyć GPT-4 z długim kontekstem

2. **Gemini Pro** - ma bardzo długi kontekst, dobry do długich transkryptów

3. **Kolejność pracy:**
   - Najpierw: Transkrypcja (skrypt `transcription.py`)
   - Potem: Prompt #4 (formatowanie)
   - Potem: Prompt #2 (highlights) 
   - Na końcu: Prompt #5 (YouTube)

4. **Zapisuj wyniki** - każdy output wklej do odpowiedniego pliku w katalogu spotkania

