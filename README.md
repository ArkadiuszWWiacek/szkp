# SZKP — System Zarządzania Kancelarią Prawną

Aplikacja webowa Django do zarządzania sprawami, klientami, prawnikami, terminami sądowymi, dokumentami, fakturami i zadaniami kancelarii prawnej.

## Wymagania

- Python **3.12**
- Django **5.1.2**
- SQLite (domyślnie) lub PostgreSQL

## Instalacja

```bash
# 1. Sklonuj repozytorium
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
# Edytuj .env — ustaw SECRET_KEY i opcjonalnie DATABASE_URL

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
# Wszystkie testy jednostkowe i integracyjne
python manage.py test

# Testy funkcjonalne Selenium (wymaga Firefox ESR + geckodriver)
python manage.py test Functional_tests

# Z pokryciem kodu
coverage run --branch manage.py test
coverage report
```

## Struktura projektu

```
Python_Web/          # konfiguracja projektu (settings, urls)
szkp/                # główna aplikacja domenowa
  models/            # modele (jeden plik = jeden model)
  views.py           # widoki
  urls.py            # routing
  admin.py           # panel administracyjny
  management/
    commands/        # komendy manage.py (seed_*)
templates/           # szablony HTML (Bootstrap 5.3 dark)
  registration/      # strona logowania
  szkp/              # widoki aplikacji
Functional_tests/    # testy Selenium (LiveServerTestCase)
static/              # pliki CSS/JS
```

## Zależności

Pełna lista w `requirements.txt`. Główne pakiety:

| Pakiet | Wersja | Opis |
|---|---|---|
| Django | 5.1.2 | framework webowy |
| Faker | 40.11.0 | generowanie danych testowych |
| selenium | 4.38.0 | testy funkcjonalne |
| coverage | 7.13.1 | pokrycie kodu testami |
| python-dotenv | 1.2.1 | zmienne środowiskowe z pliku `.env` |
