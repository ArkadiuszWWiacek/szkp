# SZKP — Instrukcje refaktoryzacji dla Claude Code

Każdy punkt to osobna, izolowana instrukcja gotowa do wklejenia w sesji Claude Code.  
Punkty są niezależne — można je wykonywać w dowolnej kolejności.  
Przed każdym punktem upewnij się, że testy przechodzą: `python manage.py test`.

---

## Spis treści

- [SZKP — Instrukcje refaktoryzacji dla Claude Code](#szkp--instrukcje-refaktoryzacji-dla-claude-code)
  - [Spis treści](#spis-treści)
  - [R-01 — Wyciągnięcie logiki kontroli dostępu do sprawy](#r-01--wyciągnięcie-logiki-kontroli-dostępu-do-sprawy)
    - [Problem](#problem)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code)
  - [R-02 — Dodanie `__str__` do 7 modeli](#r-02--dodanie-__str__-do-7-modeli)
    - [Problem](#problem-1)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-1)
  - [R-03 — Zastąpienie hardcoded stringów statusów stałymi enum](#r-03--zastąpienie-hardcoded-stringów-statusów-stałymi-enum)
    - [Problem](#problem-2)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-2)
  - [R-04 — Custom template tag dla sortowalnych nagłówków tabeli](#r-04--custom-template-tag-dla-sortowalnych-nagłówków-tabeli)
    - [Problem](#problem-3)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-3)
  - [R-05 — Dodanie paginacji do listy faktur](#r-05--dodanie-paginacji-do-listy-faktur)
    - [Problem](#problem-4)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-4)
  - [R-06 — Dodanie atrybutów `integrity` do zasobów CDN w `base.html`](#r-06--dodanie-atrybutów-integrity-do-zasobów-cdn-w-basehtml)
    - [Problem](#problem-5)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-5)
  - [R-07 — Zamiana `forms.Form` na `ModelForm`](#r-07--zamiana-formsform-na-modelform)
    - [Problem](#problem-6)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-6)
  - [R-08 — Usunięcie inline style z `invoice_list.html`](#r-08--usunięcie-inline-style-z-invoice_listhtml)
    - [Problem](#problem-7)
    - [Instrukcja dla Claude Code](#instrukcja-dla-claude-code-7)

---

## R-01 — Wyciągnięcie logiki kontroli dostępu do sprawy

### Problem

Ten blok kodu powtarza się dosłownie w czterech plikach widoków:

```python
if not request.user.is_staff:
    if not CaseLawyer.objects.filter(case=case, lawyer__user=request.user).exists():
        raise PermissionDenied
```

Wystąpienia:
- `szkp/views/cases.py` — linie 76–78, 155–157 (i wariant z `case_id=case_pk` w liniach 136–138)punkt
- `szkp/views/court_hearings.py` — linie 28–30
- `szkp/views/invoice.py` — linie 28–30

Jedynie `szkp/views/documents.py` poprawnie wyciągnął to do lokalnej funkcji `_check_access()`.

### Instrukcja dla Claude Code

```
Wykonaj refaktoryzację kontroli dostępu do sprawy w projekcie Django SZKP.

1. Utwórz nowy plik `szkp/permissions.py` z dwiema funkcjami:

   a) `require_case_access(request, case)` — sprawdza, czy zalogowany użytkownik
      ma dostęp do danego obiektu Case. Jeśli `request.user.is_staff` → przepuszcza.
      Jeśli nie — sprawdza, czy istnieje CaseLawyer łączący case z prawnikiem
      powiązanym z tym userem (lawyer__user=request.user). Jeśli nie — rzuca
      PermissionDenied. Importy: CaseLawyer z szkp.models, PermissionDenied
      z django.core.exceptions.

   b) `require_case_access_by_pk(request, case_pk)` — wariant przyjmujący case_pk
      zamiast obiektu case (używany w case_lawyer_delete gdzie mamy case_id=case_pk).
      Ta sama logika, ale filtr: CaseLawyer.objects.filter(case_id=case_pk, ...).

2. W pliku `szkp/views/cases.py`:
   - Dodaj import: `from szkp.permissions import require_case_access, require_case_access_by_pk`
   - W widoku `case_detail` (linie 76–78): zastąp blok if-not-is_staff
     wywołaniem `require_case_access(request, case)`
   - W widoku `case_lawyer_delete` (linie 136–138): zastąp blok
     wywołaniem `require_case_access_by_pk(request, case_pk)`
   - W widoku `case_lawyer_add` (linie 155–157): zastąp blok
     wywołaniem `require_case_access(request, case)`
   - Usuń zduplikowany import `PermissionDenied` jeśli nie jest już używany
     w tym pliku (zostaw go, jeśli jest używany przy sprawdzaniu roli prowadzący
     w case_lawyer_delete, linia 141)

3. W pliku `szkp/views/court_hearings.py`:
   - Dodaj import: `from szkp.permissions import require_case_access`
   - W widoku `court_hearing_form` (linie 28–30): zastąp blok if-not-is_staff
     wywołaniem `require_case_access(request, case)`
   - Usuń `from django.core.exceptions import PermissionDenied` jeśli nie jest
     już używany

4. W pliku `szkp/views/invoice.py`:
   - Dodaj import: `from szkp.permissions import require_case_access`
   - W widoku `invoice_form` (linie 28–30): zastąp blok if-not-is_staff
     wywołaniem `require_case_access(request, case)`
   - Nie zmieniaj logiki invoice_mark_paid — tam sprawdzenie jest inne
     (sprawdza case z poziomu faktury, nie odwrotnie)
   - Usuń `from django.core.exceptions import PermissionDenied` jeśli nie jest
     już używany

5. Nie modyfikuj `szkp/views/documents.py` — ma już swoją lokalną `_check_access()`
   która działa poprawnie.

6. Nie modyfikuj `szkp/views/tasks.py` — logika dostępu do zadań różni się
   od dostępu do sprawy (sprawdza assigned_lawyer, nie CaseLawyer).

7. Po zmianach uruchom: `python manage.py test` i upewnij się, że wszystkie
   testy przechodzą.
```

---

## R-02 — Dodanie `__str__` do 7 modeli

### Problem

Tylko `Case` ma metodę `__str__`. Pozostałe 7 modeli wyświetla się w panelu admina
i w debugowaniu jako `Lawyer object (1)`, `Client object (2)` itp.

Pliki do zmiany:
- `szkp/models/Lawyer.py`
- `szkp/models/Client.py`
- `szkp/models/CaseLawyer.py`
- `szkp/models/CourtHearing.py`
- `szkp/models/Document.py` (dwa modele: `Document` i `DocumentVersion`)
- `szkp/models/Invoice.py`
- `szkp/models/Task.py`

### Instrukcja dla Claude Code

```
Dodaj metodę `__str__` do 7 modeli Django w projekcie SZKP.
Nie modyfikuj modelu Case — ma już __str__.

Dla każdego modelu dodaj metodę wewnątrz klasy, przed definicją Meta
(lub po ostatnim polu jeśli Meta nie istnieje). Użyj f-stringów.

1. `szkp/models/Lawyer.py` — klasa Lawyer:
   def __str__(self):
       return f"{self.first_name} {self.last_name}"

2. `szkp/models/Client.py` — klasa Client:
   def __str__(self):
       if self.type == ClientType.FIRMA:
           return self.company_name or f"Firma (id={self.pk})"
       return f"{self.first_name} {self.last_name}"

3. `szkp/models/CaseLawyer.py` — klasa CaseLawyer:
   def __str__(self):
       return f"{self.case} — {self.lawyer} ({self.get_role_display()})"

4. `szkp/models/CourtHearing.py` — klasa CourtHearing:
   def __str__(self):
       return f"{self.case} / {self.scheduled_at:%Y-%m-%d} / {self.court_name}"

5. `szkp/models/Document.py` — klasa Document:
   def __str__(self):
       return self.title

   klasa DocumentVersion:
   def __str__(self):
       return f"{self.document} v{self.version_number}"

6. `szkp/models/Invoice.py` — klasa Invoice:
   def __str__(self):
       return self.invoice_number

7. `szkp/models/Task.py` — klasa Task:
   def __str__(self):
       return self.title

Po zmianach uruchom `python manage.py test` i sprawdź, że testy przechodzą.
Żadna migracja nie jest potrzebna — __str__ nie wpływa na schemat bazy danych.
```

---

## R-03 — Zastąpienie hardcoded stringów statusów stałymi enum

### Problem

W `szkp/views/dashboard.py` dwa zapytania używają literałów tekstowych zamiast
stałych z klas `TextChoices`:

```python
# linia 43 — hardcoded 'planowany'
.filter(scheduled_at__date__gte=today, status='planowany')

# linie 57 i 67 — hardcoded ['nowe', 'w_toku']
.filter(due_date__date=today, status__in=['nowe', 'w_toku'])
status__in=['nowe', 'w_toku'],
```

Gdyby wartości enum zmieniły się w migracjach lub ktoś zrobił literówkę,
te zapytania cicho zwróciłyby pustą listę bez żadnego błędu.

### Instrukcja dla Claude Code

```
Napraw użycie hardcoded stringów statusów w `szkp/views/dashboard.py`.

1. W sekcji importów na górze pliku dodaj brakujące klasy enum.
   Obecny import wygląda tak:
       from szkp.models import (
           Case, CaseStatus,
           CourtHearing,
           Invoice, InvoiceStatus,
           Task,
       )
   Rozszerz go o HearingStatus i TaskStatus:
       from szkp.models import (
           Case, CaseStatus,
           CourtHearing, HearingStatus,
           Invoice, InvoiceStatus,
           Task, TaskStatus,
       )

2. W funkcji `dashboard`, w zapytaniu `upcoming_hearings` (okolice linii 43):
   Zamień:
       .filter(scheduled_at__date__gte=today, status='planowany')
   Na:
       .filter(scheduled_at__date__gte=today, status=HearingStatus.PLANOWANY)

3. W zapytaniu `today_tasks` (okolice linii 57):
   Zamień:
       .filter(due_date__date=today, status__in=['nowe', 'w_toku'])
   Na:
       .filter(due_date__date=today, status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU])

4. W zapytaniu `upcoming_tasks` (okolice linii 67):
   Zamień:
       status__in=['nowe', 'w_toku'],
   Na:
       status__in=[TaskStatus.NOWE, TaskStatus.W_TOKU],

5. Nie modyfikuj zapytania overdue_invoices — już używa InvoiceStatus.PRZETERMINOWANA.

Po zmianach uruchom `python manage.py test szkp.tests.test_dashboard_views`
i `python manage.py test` żeby upewnić się, że nic nie zostało zepsute.
```

---

## R-04 — Custom template tag dla sortowalnych nagłówków tabeli

### Problem

We wszystkich trzech szablonach list (`case_list.html`, `client_list.html`,
`invoice_list.html`) każda sortowalna kolumna powtarza identyczny wzorzec HTML:

```html
<th class="{% if sort == 'KLUCZ' %}szkp-sort-active{% endif %}">
    <a href="?...&sort=KLUCZ&dir={% if sort == 'KLUCZ' and direction == 'asc' %}desc{% else %}asc{% endif %}">
        Etykieta
        <span class="szkp-sort-icon {% if sort == 'KLUCZ' %}szkp-sort-icon--{% if direction == 'asc' %}asc{% else %}desc{% endif %}{% endif %}"></span>
    </a>
</th>
```

W `case_list.html` wzorzec pojawia się 5 razy, w `client_list.html` 3 razy,
w `invoice_list.html` 6 razy — razem 14 powtórzeń.

### Instrukcja dla Claude Code

```
Utwórz custom template tag `sort_th` upraszczający sortowalne nagłówki tabel
w projekcie SZKP.

1. Utwórz katalog `szkp/templatetags/` (jeśli nie istnieje):
   - `szkp/templatetags/__init__.py` (pusty plik)
   - `szkp/templatetags/szkp_tags.py` (implementacja)

2. W `szkp/templatetags/szkp_tags.py` zaimplementuj inclusion tag:

   from django import template
   from urllib.parse import urlencode, parse_qs, urlparse

   register = template.Library()

   @register.inclusion_tag('szkp/partials/sort_th.html', takes_context=True)
   def sort_th(context, key, label):
       """
       Renderuje sortowalny nagłówek tabeli <th>.
       Użycie: {% sort_th "case_number" "Sygnatura" %}
       Wymaga w kontekście: sort, direction oraz request.GET (przez request).
       """
       sort = context.get('sort', '')
       direction = context.get('direction', 'asc')
       request = context.get('request')

       # Zbuduj parametry GET zachowując istniejące filtry, zastępując sort i dir
       params = {}
       if request:
           params = {k: v for k, v in request.GET.items()
                     if k not in ('sort', 'dir', 'page')}

       is_active = (sort == key)
       next_dir = 'desc' if (is_active and direction == 'asc') else 'asc'
       params['sort'] = key
       params['dir'] = next_dir
       query_string = urlencode(params)

       return {
           'key': key,
           'label': label,
           'is_active': is_active,
           'current_dir': direction if is_active else '',
           'url': f'?{query_string}',
       }

3. Utwórz katalog `szkp/templates/szkp/partials/` i plik `sort_th.html`:

   <th class="{% if is_active %}szkp-sort-active{% endif %}">
       <a href="{{ url }}">
           {{ label }}
           <span class="szkp-sort-icon{% if is_active %} szkp-sort-icon--{{ current_dir }}{% endif %}"></span>
       </a>
   </th>

4. W `szkp/templates/szkp/case_list.html`:
   - Na początku pliku (po {% extends "base.html" %}) dodaj:
     {% load szkp_tags %}
   - Zastąp każdy blok <th class="{% if sort == 'X' %}...">...</th>
     wywołaniem tagu. Przykładowo:
     PRZED:
       <th class="{% if sort == 'case_number' %}szkp-sort-active{% endif %}">
           <a href="?q={{ q }}&status={{ status }}&type={{ case_type }}&sort=case_number&dir={% if sort == 'case_number' and direction == 'asc' %}desc{% else %}asc{% endif %}">
               Sygnatura
               <span class="szkp-sort-icon {% if sort == 'case_number' %}szkp-sort-icon--{% if direction == 'asc' %}asc{% else %}desc{% endif %}{% endif %}"></span>
           </a>
       </th>
     PO:
       {% sort_th "case_number" "Sygnatura" %}
   - Zrób to samo dla kolumn: client, case_type, status, case_priority
   - Kolumna "Prawnicy" jest nieortowalna — zostaw jako zwykłe <th>Prawnicy</th>
   - Usuń ukryte pola sort i dir z formularza wyszukiwania — tag sam je obsługuje
     przez request.GET. Uwaga: sprawdź czy sort i dir są też w linkach paginacji;
     jeśli tak, paginacja musi nadal przekazywać sort i dir ręcznie przez query string.

5. W `szkp/templates/szkp/client_list.html`:
   - Dodaj {% load szkp_tags %}
   - Zastąp sortowalne nagłówki: last_name → "Klient", type → "Typ",
     created_at → "Dodano"
   - Kolumny "PESEL / NIP" i "Kontakt" są nieortowalne — zostaw jako <th>

6. W `szkp/templates/szkp/invoice_list.html`:
   - Dodaj {% load szkp_tags %}
   - Zastąp sortowalne nagłówki: invoice_number → "Numer", case → "Sprawa",
     issue_date → "Data wystawienia", due_date → "Termin", gross_amount → "Kwota",
     status → "Status"

7. Sprawdź, że `request` jest dostępny w kontekście szablonów. W settings.py
   powinien być context processor `django.template.context_processors.request`
   — już jest, więc nie wymaga zmian.

8. Uruchom serwer deweloperski i ręcznie sprawdź sortowanie na każdej liście.
   Następnie uruchom: `python manage.py test` żeby upewnić się, że testy przechodzą.
```

---

## R-05 — Dodanie paginacji do listy faktur

### Problem

`invoice_list` przekazuje do szablonu surowy QuerySet `invoices` bez paginacji,
podczas gdy `case_list` i `client_list` mają Paginator z 20 rekordami na stronę.
Przy dużym zbiorze faktur widok zwróci wszystkie rekordy naraz.

Szablon `invoice_list.html` iteruje przez `{% for inv in invoices %}`.

### Instrukcja dla Claude Code

```
Dodaj paginację do widoku i szablonu listy faktur w projekcie SZKP.

--- WIDOK: szkp/views/invoice.py ---

1. W sekcji importów dodaj:
   from django.core.paginator import Paginator

2. W funkcji `invoice_list`, przed instrukcją `return render(...)`:
   Zastąp obecny kod:
       return render(request, 'szkp/invoice_list.html', {
           'invoices':       qs,
           ...
       })
   Następującym:
       paginator = Paginator(qs, 20)
       page_obj = paginator.get_page(request.GET.get('page', 1))

       return render(request, 'szkp/invoice_list.html', {
           'page_obj':       page_obj,
           'invoices':       page_obj,   # zachowaj 'invoices' dla wstecznej
                                          # kompatybilności z istniejącymi testami
           'status_choices': InvoiceStatus.choices,
           'current_status': status or '',
           'sort':           sort,
           'direction':      direction,
           'q':              q,
       })

--- SZABLON: szkp/templates/szkp/invoice_list.html ---

3. Znajdź zamykający tag </table> (lub </div> kończący tabelę faktur).
   Bezpośrednio po nim dodaj blok paginacji wzorowany na `client_list.html`:

   <div class="szkp-pagination">
       <div class="szkp-pagination__info">
           Pokazano {{ page_obj.start_index }}–{{ page_obj.end_index }}
           z {{ page_obj.paginator.count }}
       </div>
       <div class="szkp-pagination__pages">
           {% if page_obj.has_previous %}
               <a class="szkp-page-btn"
                  href="?q={{ q }}&status={{ current_status }}&sort={{ sort }}&dir={{ direction }}&page={{ page_obj.previous_page_number }}">‹</a>
           {% else %}
               <span class="szkp-page-btn szkp-page-btn--disabled">‹</span>
           {% endif %}
           {% for num in page_obj.paginator.page_range %}
               {% if page_obj.number == num %}
                   <span class="szkp-page-btn active">{{ num }}</span>
               {% elif num >= page_obj.number|add:"-3" and num <= page_obj.number|add:"3" %}
                   <a class="szkp-page-btn"
                      href="?q={{ q }}&status={{ current_status }}&sort={{ sort }}&dir={{ direction }}&page={{ num }}">{{ num }}</a>
               {% elif num == 1 or num == page_obj.paginator.num_pages %}
                   <a class="szkp-page-btn"
                      href="?q={{ q }}&status={{ current_status }}&sort={{ sort }}&dir={{ direction }}&page={{ num }}">{{ num }}</a>
               {% endif %}
           {% endfor %}
           {% if page_obj.has_next %}
               <a class="szkp-page-btn"
                  href="?q={{ q }}&status={{ current_status }}&sort={{ sort }}&dir={{ direction }}&page={{ page_obj.next_page_number }}">›</a>
           {% else %}
               <span class="szkp-page-btn szkp-page-btn--disabled">›</span>
           {% endif %}
       </div>
   </div>

4. Sprawdź testy w `szkp/tests/test_us07_views.py` i `szkp/tests/test_invoice_sort_views.py`.
   Jeśli testy odwołują się do `context['invoices']`, nie musisz ich zmieniać —
   klucz 'invoices' nadal jest przekazywany do kontekstu (jako page_obj).
   Jeśli testy sprawdzają typ lub liczbę rekordów, może być konieczna aktualizacja
   asercji (np. `len(response.context['invoices'])` → `response.context['invoices'].paginator.count`).

5. Uruchom: `python manage.py test szkp.tests.test_us07_views`
   i `python manage.py test szkp.tests.test_invoice_sort_views`
   a następnie `python manage.py test` — wszystkie testy muszą przejść.
```

---

## R-06 — Dodanie atrybutów `integrity` do zasobów CDN w `base.html`

### Problem

`templates/base.html` ładuje Bootstrap 5.3.0 i czcionki Google bez atrybutu
Subresource Integrity (`integrity`). Pozwala to na podstawienie złośliwego kodu
w przypadku kompromitacji CDN.

Obecny stan (linie 15–16 i 147):
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
      rel="stylesheet">
...
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

### Instrukcja dla Claude Code

```
Dodaj atrybuty Subresource Integrity (SRI) do tagów Bootstrap w `templates/base.html`.

1. Oficjalne hashe SHA-384 dla Bootstrap 5.3.0 (pobrane z https://getbootstrap.com/docs/5.3/getting-started/introduction/):

   CSS:
   integrity="sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM"

   JS bundle:
   integrity="sha384-ENjdO4Dr2bkBIFxQpeoTz1HIcje39Wm4jDKdf19U8gI4ddQ3GYNS7NTKfAdVzdl"

2. W `templates/base.html` znajdź tag <link> dla Bootstrap CSS i zmień go na:
   <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
         rel="stylesheet"
         integrity="sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM"
         crossorigin="anonymous">

3. Znajdź tag <script> dla Bootstrap JS i zmień go na:
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
           integrity="sha384-ENjdO4Dr2bkBIFxQpeoTz1HIcje39Wm4jDKdf19U8gI4ddQ3GYNS7NTKfAdVzdl"
           crossorigin="anonymous"></script>

4. Atrybutu integrity NIE dodawaj do Google Fonts — Google Fonts celowo rotuje
   zasoby i nie zapewnia stabilnych hashy SRI. Pozostaw tagi Google Fonts
   bez zmian.

5. Weryfikacja ręczna: uruchom serwer (`python manage.py runserver`), otwórz
   dowolną stronę i w DevTools (Network) sprawdź, że Bootstrap ładuje się
   bez błędów SRI w konsoli.

6. Uruchom `python manage.py test` — zmiany w base.html nie powinny wpłynąć
   na żaden test.

Uwaga: jeśli w przyszłości projekt zostanie zaktualizowany do nowszej wersji
Bootstrap, hashe muszą być zaktualizowane razem z numerem wersji. Poprawne hashe
zawsze można znaleźć na https://getbootstrap.com lub wygenerować komendą:
  curl -s URL | openssl dgst -sha384 -binary | openssl base64 -A
```

---

## R-07 — Zamiana `forms.Form` na `ModelForm`

### Problem

Wszystkie formularze w `szkp/forms.py` dziedziczą po `forms.Form`. Każdy widok
CRUD ręcznie przepisuje dane z `cleaned_data` na pola modelu (10–15 linii per widok).

Przykład redundancji w `client_form`:
```python
obj.type         = cd['type']
obj.first_name   = cd.get('first_name') or None
obj.last_name    = cd.get('last_name') or None
obj.company_name = cd.get('company_name') or None
# ... 7 kolejnych linii
obj.save()
```

### Instrukcja dla Claude Code

```
Zrefaktoryzuj formularze SZKP — zamień forms.Form na ModelForm.
Jest to duża zmiana. Wykonuj ją model po modelu i uruchamiaj testy po każdym.

WAŻNE ZASADY PRZED ROZPOCZĘCIEM:
- Logika walidacji z clean() / clean_pole() musi zostać przeniesiona 1:1
- Formularze z parametrami w __init__ (InvoiceForm, TaskForm, CaseLawyerForm,
  CourtHearingForm, DocumentForm) wymagają nadpisania __init__
- NIE zmieniaj logiki biznesowej w modelach (Invoice.save, Task.save, Client.clean)
- Po każdym formularzu uruchom: python manage.py test

--- KROK 1: ClientForm ---

W `szkp/forms.py` zastąp ClientForm:

   class ClientForm(forms.ModelForm):
       class Meta:
           model = Client
           fields = ['type', 'first_name', 'last_name', 'company_name',
                     'pesel', 'nip', 'phone', 'email',
                     'address_street', 'address_city', 'address_zip']

       def clean(self):
           # Skopiuj istniejącą logikę clean() bez zmian
           ...

W `szkp/views/clients.py` w funkcji `client_form`:
- Przy POST: zamień `form = ClientForm(request.POST)` na `form = ClientForm(request.POST, instance=client)`
- Jeśli form.is_valid(): zastąp ręczne przepisanie przez `form.save()`
- Usuń blok `obj = client or Client()` i wszystkie linie `obj.pole = cd[...]`
- Przy GET: zamień budowanie `form_data = {...}` na `form = ClientForm(instance=client)`
  i przekaż `form` do kontekstu zamiast `form_data` i `errors`
- W szablonie `client_form.html` zachowaj obecny wygląd pól ale zmień
  sposób pobierania wartości: zamiast `value="{{ form_data.type }}"` użyj
  `value="{{ form.type.value }}"` lub renderuj przez `{{ form.type }}`
  (jeśli chcesz zachować ręczny HTML pól, użyj `form.pole.value` i
  `form.pole.errors`)

--- KROK 2: CaseForm ---

   class CaseForm(forms.ModelForm):
       class Meta:
           model = Case
           fields = ['case_number', 'title', 'client', 'case_type',
                     'status', 'case_priority', 'court_case_number', 'description']
       
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           # Pole status: dodaj pustą opcję
           self.fields['status'].choices = [('', '---------')] + list(CaseStatus.choices)
           self.fields['case_priority'].choices = [('', '---------')] + list(CasePriority.choices)

W `szkp/views/cases.py` w funkcji `case_form`:
- Zachowaj logikę ustawiania closed_at przy status ZAKOŃCZONA — zrób to
  po form.save(commit=False), przed obj.save()
- Zachowaj logikę tworzenia CaseLawyer dla nowego case po zapisie

--- KROK 3: CourtHearingForm ---

   class CourtHearingForm(forms.ModelForm):
       class Meta:
           model = CourtHearing
           fields = ['court_name', 'hearing_type', 'scheduled_at', 'status',
                     'reminder_minutes_before', 'courtroom', 'judge_name', 'notes']
           widgets = {
               'scheduled_at': forms.DateTimeInput(
                   attrs={'type': 'datetime-local'},
                   format='%Y-%m-%dT%H:%M'
               ),
           }
       
       def __init__(self, *args, is_new=False, **kwargs):
           super().__init__(*args, **kwargs)
           self.is_new = is_new
       
       def clean(self):
           # Skopiuj istniejącą logikę clean() bez zmian

--- KROK 4: InvoiceForm ---

   class InvoiceForm(forms.ModelForm):
       class Meta:
           model = Invoice
           fields = ['invoice_number', 'issue_date', 'due_date',
                     'net_amount', 'vat_rate', 'currency', 'status']
           widgets = {
               'issue_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
               'due_date':   forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
           }
       
       def __init__(self, *args, instance_pk=None, **kwargs):
           super().__init__(*args, **kwargs)
           self._instance_pk = instance_pk
       
       def clean_invoice_number(self):
           # Skopiuj istniejącą logikę bez zmian, używając self._instance_pk

--- KROK 5: TaskForm i DocumentForm ---

Analogicznie do powyższych wzorców.
TaskForm wymaga __init__ przyjmującego case_lawyer_pks.
DocumentForm wymaga __init__ przyjmującego is_new.

--- WERYFIKACJA KOŃCOWA ---

Po wszystkich krokach:
   python manage.py test
   python manage.py runserver

Ręcznie przetestuj:
- Dodaj klienta (osobę fizyczną i firmę) — sprawdź walidację PESEL/NIP
- Dodaj sprawę — sprawdź unikalność case_number
- Edytuj fakturę — sprawdź, że gross_amount jest obliczane
- Zmień status sprawy na zakończoną — sprawdź, że closed_at jest ustawiane
```

---

## R-08 — Usunięcie inline style z `invoice_list.html`

### Problem

W `szkp/templates/szkp/invoice_list.html`, linia 99, jedyne wystąpienie
`style=` w całym projekcie:

```html
<tr onclick="window.location='...'" style="cursor:pointer">
```

Analogiczny efekt klikowalnego wiersza w `case_list.html` uzyskany jest przez
sam atrybut `onclick` bez inline style — co oznacza niespójność.

### Instrukcja dla Claude Code

```
Usuń jedyny inline style z projektu SZKP.

1. Sprawdź plik `static/style.css` czy istnieje już klasa nadająca
   `cursor: pointer` wierszom tabeli. Jeśli tak — użyj jej.
   Jeśli nie — dodaj na końcu pliku `static/style.css`:

   /* Klikalny wiersz tabeli */
   .szkp-table tbody tr[onclick] {
       cursor: pointer;
   }

   Ta reguła CSS automatycznie obejmie WSZYSTKIE wiersze z atrybutem onclick
   w tabelach szkp-table — zarówno w invoice_list.html jak i case_list.html —
   bez konieczności dodawania klasy CSS ręcznie do każdego <tr>.

2. W `szkp/templates/szkp/invoice_list.html`, linia 99:
   Usuń atrybut `style="cursor:pointer"` z tagu <tr>:

   PRZED:
   <tr onclick="window.location='...'" style="cursor:pointer">

   PO:
   <tr onclick="window.location='...'">

3. Zweryfikuj wizualnie: uruchom serwer, przejdź do /szkp/faktury/ i sprawdź
   czy kursor zmienia się na pointer po najechaniu na wiersz tabeli.

4. Sprawdź czy case_list.html i my_tasks.html mają <tr onclick> bez cursor —
   jeśli reguła `.szkp-table tbody tr[onclick]` działa poprawnie, będą
   automatycznie objęte (to pożądane zachowanie).

5. Uruchom `python manage.py test` — żaden test nie powinien sprawdzać
   obecności inline style, więc wszystkie muszą przejść.
```

---

*8 instrukcji · priorytety: R-01 R-02 R-03 (wysokie) · R-04 R-05 R-06 (średnie) · R-07 R-08 (niskie/kosmetyka)*
