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

---

## R-05 — Dodanie paginacji do listy faktur

### Problem

`invoice_list` przekazuje do szablonu surowy QuerySet `invoices` bez paginacji,
podczas gdy `case_list` i `client_list` mają Paginator z 20 rekordami na stronę.
Przy dużym zbiorze faktur widok zwróci wszystkie rekordy naraz.

Szablon `invoice_list.html` iteruje przez `{% for inv in invoices %}`.

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

---

*8 instrukcji · priorytety: R-01 R-02 R-03 (wysokie) · R-04 R-05 R-06 (średnie) · R-07 R-08 (niskie/kosmetyka)*
