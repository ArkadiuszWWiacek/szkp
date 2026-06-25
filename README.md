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
# Wszystkie testy jednostkowe, integracyjne i funkcjonalne Selenium (wymaga narzędzi systemowych Firefox ESR + geckodriver > instrukcja instalacji na końcu)
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
  templatetags/      # tagi szablonów (sort_th, pagination, pagination_dash, widget_value)
  forms.py           # formularze (ModelForm + plain Form)
  permissions.py     # helpery kontroli dostępu (require_case_access)
  view_utils.py      # helpery widoków (apply_sorting, apply_pagination)
  urls.py            # routing
  admin.py           # panel administracyjny
  templates/szkp/    # szablony widoków; partials/ — wielokrotnego użytku (pagination, confirm_delete)
  tests/             # testy jednostkowe i integracyjne
  management/
    commands/        # komendy manage.py (seed_*)
accounts/            # uwierzytelnianie (formularz logowania)
templates/           # szablony projektowe (base.html Bootstrap 5.3, base_dash.html panel SU)
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


## Instalacja geckodriver i Firefox ESR w Ubuntu

Ten dokument opisuje pełną instalację geckodriver oraz Firefox ESR w Ubuntu z użyciem wiersza poleceń. W Ubuntu pakiet `firefox-esr` nie zawsze jest dostępny w domyślnych repozytoriach APT, dlatego często trzeba dodać repozytorium Mozilla Team PPA przed instalacją. [linuxcapable](https://linuxcapable.com/how-to-install-firefox-esr-on-ubuntu-linux/)

### Wymagania

Przed rozpoczęciem warto mieć uprawnienia `sudo` oraz zainstalowane podstawowe narzędzia systemowe. Geckodriver działa jako sterownik WebDriver dla przeglądarki Firefox i musi być dostępny w systemowym `PATH`, aby Selenium mogło go używać poprawnie. [firefox-source-docs.mozilla](https://firefox-source-docs.mozilla.org/testing/geckodriver/Usage.html)

### Krok 1: aktualizacja systemu

```bash
sudo apt update
sudo apt upgrade -y
```

Aktualizacja listy pakietów i systemu zmniejsza ryzyko problemów z zależnościami podczas instalacji Firefoksa i sterownika. [linuxcapable](https://linuxcapable.com/how-to-install-firefox-esr-on-ubuntu-linux/)

### Krok 2: dodanie repozytorium Mozilla Team PPA

W wielu wersjach Ubuntu pakiet `firefox-esr` nie jest dostępny bezpośrednio w standardowych repozytoriach, więc należy dodać Mozilla Team PPA. [ubuntuhandbook](https://ubuntuhandbook.org/index.php/2023/09/install-firefox-esr-115-ppa/)

```bash
sudo add-apt-repository ppa:mozillateam/ppa
sudo apt update
```

Po dodaniu repozytorium system pobierze zaktualizowaną listę pakietów, w tym pakiet `firefox-esr`, jeśli jest oferowany dla danej wersji Ubuntu. [vegastack](https://vegastack.com/tutorials/how-to-install-firefox-esr-on-ubuntu-22-04/)

### Krok 3: instalacja Firefox ESR

```bash
sudo apt install -y firefox-esr
```

Firefox ESR to kanał o wydłużonym wsparciu, przeznaczony dla środowisk wymagających większej stabilności aktualizacji. [support.mozilla](https://support.mozilla.org/pl/kb/cykl-wydawniczy-firefox-esr)

### Krok 4: weryfikacja instalacji Firefoksa

```bash
which firefox-esr
firefox-esr --version
```

Jeśli `which firefox-esr` zwraca ścieżkę, oznacza to, że przeglądarka jest widoczna w `PATH` i może być używana przez Selenium jako właściwa binarka Firefoksa. [stackoverflow](https://stackoverflow.com/questions/73530481/invalidargumentexception-message-binary-is-not-a-firefox-executable-error-in-p)

### Krok 5: pobranie geckodriver

Geckodriver jest udostępniany jako osobny plik wykonywalny w sekcji wydań projektu Mozilla na GitHubie. Należy pobrać wersję przeznaczoną dla systemu Linux 64-bit. [github](https://github.com/mozilla/geckodriver)

```bash
cd /tmp
wget https://github.com/mozilla/geckodriver/releases/download/vX.Y.Z/geckodriver-vX.Y.Z-linux64.tar.gz
```

W miejsce `X.Y.Z` należy wstawić aktualny numer wersji z listy wydań geckodriver. [baeldung](https://www.baeldung.com/linux/geckodriver-installation)

### Krok 6: rozpakowanie archiwum

```bash
tar -xvzf geckodriver-vX.Y.Z-linux64.tar.gz
chmod +x geckodriver
```

Po rozpakowaniu powstaje plik wykonywalny `geckodriver`, któremu trzeba nadać prawo uruchamiania. [stackoverflow](https://stackoverflow.com/questions/40867959/installing-geckodriver-only-using-terminal)

### Krok 7: instalacja geckodriver w katalogu systemowym

Najwygodniej przenieść sterownik do `/usr/local/bin`, ponieważ ten katalog zwykle jest już obecny w `PATH`. [medium](https://medium.com/@marco.alencastro/configurando-o-geckodriver-no-ubuntu-dd93b2318b3d)

```bash
sudo mv geckodriver /usr/local/bin/
```

### Krok 8: weryfikacja geckodriver

```bash
which geckodriver
geckodriver --version
```

Jeżeli polecenia zwracają ścieżkę i numer wersji, sterownik jest gotowy do użycia. [cyberithub](https://www.cyberithub.com/how-to-install-geckodriver-for-selenium-in-linux/)

### Krok 9: instalacja Selenium dla Pythona

```bash
python3 -m pip install --user selenium
```

Selenium współpracuje z Firefoksem przez geckodriver, a sam sterownik musi być osiągalny przez `PATH` albo przekazany jawnie w konfiguracji. [firefox-source-docs.mozilla](https://firefox-source-docs.mozilla.org/testing/geckodriver/Usage.html)

### Krok 10: test działania

```python
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

options = Options()
options.binary_location = "/usr/bin/firefox-esr"
service = Service("/usr/local/bin/geckodriver")

driver = webdriver.Firefox(service=service, options=options)
driver.get("https://example.com")
print(driver.title)
driver.quit()
```

W tej konfiguracji `binary_location` wskazuje na właściwą binarkę Firefoksa, a `Service(...)` wskazuje ścieżkę do geckodriver. Rozdzielenie tych dwóch ścieżek jest ważne, bo częstym błędem jest podanie geckodriver jako binarki Firefoksa, co powoduje komunikat `binary is not a Firefox executable`. [thecoderscamp](https://www.thecoderscamp.com/selenium-common-exceptions-invalidargumentexception-message-binary-is-not-a-fir/)

### Krok 11: tryb headless

Na serwerze bez środowiska graficznego można użyć trybu headless:

```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

options = Options()
options.add_argument("--headless")
options.binary_location = "/usr/bin/firefox-esr"
service = Service("/usr/local/bin/geckodriver")

driver = webdriver.Firefox(service=service, options=options)
driver.get("https://example.com")
print(driver.title)
driver.quit()
```

Tryb headless pozwala uruchamiać testy bez otwierania okna przeglądarki, co jest typowe dla serwerów i CI/CD. [firefox-source-docs.mozilla](https://firefox-source-docs.mozilla.org/testing/geckodriver/Usage.html)

### Diagnostyka problemów

#### `Package firefox-esr has no installation candidate`

Ten komunikat zwykle oznacza, że `firefox-esr` nie jest dostępny w obecnie skonfigurowanych repozytoriach APT. W Ubuntu typową naprawą jest dodanie Mozilla Team PPA i ponowne wykonanie `apt update`. [ubuntuhandbook](https://ubuntuhandbook.org/index.php/2023/09/install-firefox-esr-115-ppa/)

#### `binary is not a Firefox executable`

Ten błąd oznacza, że Selenium otrzymało złą ścieżkę w `binary_location`, na przykład do `geckodriver` zamiast do Firefoksa. [stackoverflow](https://stackoverflow.com/questions/73530481/invalidargumentexception-message-binary-is-not-a-firefox-executable-error-in-p)

#### `geckodriver: command not found`

Ten komunikat oznacza, że plik nie znajduje się w `PATH` albo nie ma prawa wykonywania [medium](https://medium.com/beelabacademy/baixando-e-configurando-o-geckodriver-no-ubuntu-dc2fe14d91c)