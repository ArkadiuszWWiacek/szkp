# SZKP — System Zarządzania Kancelarią Prawną

Aplikacja webowa Django do zarządzania sprawami, klientami, prawnikami, terminami sądowymi, dokumentami, fakturami i zadaniami kancelarii prawnej.

## Funkcje

- **Sprawy** — lista z wyszukiwaniem, filtrowaniem, sortowaniem i paginacją; zakładki na szczegółach sprawy (terminy, dokumenty, zadania, faktury, prawnicy); zmiana statusu inline
- **Klienci** — CRUD z walidacją PESEL (osoby fizyczne) i NIP (firmy)
- **Terminy sądowe** — tworzenie i edycja powiązana ze sprawą; walidacja daty w przyszłości
- **Dokumenty** — upload pliku z wersjonowaniem; podgląd inline `.txt`/`.md`
- **Faktury** — lista z filtrem statusu i paginacją; automatyczne obliczanie kwoty brutto (netto × VAT); oznaczanie jako opłacona
- **Zadania** — lista własnych zadań z filtrami (status, okres, numer sprawy); podzadania (inline formset); blokada zamknięcia gdy są nieukończone podzadania
- **Panel superusera** — oddzielny dashboard (metryki, feed aktywności, wykres kołowy spraw, lista użytkowników, info systemowe); zarządzanie użytkownikami (tworzenie, edycja, aktywacja/deaktywacja)

## Wymagania

- Python **3.12**
- Django **5.1.2**
- SQLite (domyślnie) lub PostgreSQL

## Instalacja

```bash
# 1. Sklonuj repozytorium lub rozpakuj z .zip
git clone <url-repozytorium>
cd Python_Web

# 2. Utwórz i aktywuj środowisko wirtualne
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Skonfiguruj zmienne środowiskowe
cp .env.example .env
# Edytuj .env — SECRET_KEY jest wymagany, pozostałe mają wartości domyślne

# 5. Zastosuj migracje
python manage.py migrate

# 6. Utwórz konto administratora
python manage.py createsuperuser
```

## Uruchomienie serwera deweloperskiego

```bash
# Dostępny tylko lokalnie (127.0.0.1:8000)
python manage.py runserver

# Dostępny w sieci lokalnej (np. Raspberry Pi, VM)
python manage.py runserver 0.0.0.0:8000
```

Aplikacja dostępna pod: `http://127.0.0.1:8000/`  
Panel admina: `http://127.0.0.1:8000/admin/`

## Dane demo

Załaduj pełny zestaw danych demonstracyjnych jedną komendą:

```bash
python manage.py seed_all
```

Aby wyczyścić bazę i załadować od nowa:

```bash
python manage.py seed_all --clear
```

Po załadowaniu danych utwórz konta użytkowników dla prawników:

```bash
python manage.py seed_users
```

### Konta demo

| Login | Hasło | Specjalizacja |
|---|---|---|
| `anna.kowalska` | `szkp1234` | prawo cywilne |
| `piotr.nowak` | `szkp1234` | prawo karne |
| `marta.wisniewska` | `szkp1234` | prawo gospodarcze |
| `tomasz.wojcik` | `szkp1234` | prawo rodzinne |
| `katarzyna.kaminska` | `szkp1234` | prawo pracy |

### Komendy seed — szczegóły

| Komenda | Opis | Opcje |
|---|---|---|
| `seed_all` | Uruchamia wszystkie seedy w kolejności | `--clear` |
| `seed_clients` | 50 klientów (osoby fizyczne i firmy) | — |
| `seed_lawyers` | 5 prawników | — |
| `seed_users` | Konta Django dla istniejących prawników | `--clear`, `--password` |
| `seed_cases` | Sprawy | `--count N`, `--clear` |
| `seed_case_lawyers` | Przypisania prawników do spraw | `--clear` |
| `seed_court_hearings` | Terminy sądowe | `--count N`, `--clear` |
| `seed_documents` | Dokumenty i wersje | `--count N`, `--clear` |
| `seed_invoices` | Faktury | `--count N`, `--clear` |
| `seed_tasks` | Zadania (z opcjonalnymi podzadaniami) | `--count N`, `--with-subtasks`, `--clear` |

## Testy

```bash
# Wszystkie testy jednostkowe, integracyjne i funkcjonalne Selenium (wymaga narzędzi systemowych Firefox ESR + geckodriver)
python manage.py test

# Poszczególne testy
python manage.py test --tag=unit
python manage.py test --tag=integration
python manage.py test --tag=functional

# Z pokryciem kodu
coverage run --branch manage.py test
coverage report
coverage html
```

## Struktura projektu

```
Python_Web/          # konfiguracja projektu (settings, urls)
szkp/                # główna aplikacja domenowa
  models/            # modele (jeden plik = jeden model)
  views/             # widoki (jeden plik = jeden obszar domenowy)
  templatetags/      # tagi szablonów (sort_th, widget_value)
  forms.py           # formularze (ModelForm + plain Form)
  permissions.py     # helpery kontroli dostępu (require_case_access)
  urls.py            # routing
  admin.py           # panel administracyjny
  tests/             # testy jednostkowe i integracyjne
  management/
    commands/        # komendy manage.py (seed_*)
accounts/            # uwierzytelnianie (formularz logowania)
templates/           # szablony HTML (base.html Bootstrap 5.3, base_dash.html panel SU)
Functional_tests/    # testy Selenium (LiveServerTestCase)
static/              # CSS (style.css z tokenami --szkp-* i --dash-*)
```

## Zależności

Pełna lista w `requirements.txt`. Główne pakiety:

| Pakiet | Wersja | Opis |
|---|---|---|
| Django | 5.1.2 | framework webowy |
| dj-database-url | 2.3.0 | parsowanie `DATABASE_URL` (SQLite / PostgreSQL) |
| markdown | 3.10 | podgląd plików `.md` w widoku dokumentu |
| matplotlib | 3.10.8 | wykres kołowy spraw w panelu superusera |
| Faker | 40.11.0 | generowanie danych testowych |
| psycopg | 3.3.2 | sterownik PostgreSQL |
| selenium | 4.38.0 | testy funkcjonalne |
| coverage | 7.13.1 | pokrycie kodu testami |
| python-dotenv | 1.2.1 | zmienne środowiskowe z pliku `.env` |
