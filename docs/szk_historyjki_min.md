# SZKP – Historyjki użytkownika

**System Zarządzania Kancelarią Prawną** | Django | Python

---

## 1. Logowanie i uprawnienia

### US-01 — Logowanie i wylogowanie

**Jako** pracownik **chcę** zalogować się i wylogować,
**aby** bezpiecznie korzystać z systemu.

- [ ] Formularz login + hasło z tokenem CSRF
- [ ] Przekierowanie na dashboard po zalogowaniu; komunikat przy błędzie
- [ ] Wylogowanie unieważnia sesję i przekierowuje na stronę logowania

---

### US-02 — Zarządzanie rolami użytkowników

**Jako** administrator  
**chcę** przypisywać role (admin / prawnik / asystent) użytkownikom systemu,  
**aby** kontrolować dostęp do poszczególnych funkcji.

**Kryteria akceptacji:**
- [ ] Role zrealizowane przez grupy Django lub flagi `is_staff` / `is_superuser`
- [ ] Widoki chronione dekoratorem `@login_required` lub `permission_required`
- [ ] Użytkownik bez odpowiedniej roli otrzymuje odpowiedź 403 lub jest przekierowany
- [ ] Zarządzanie rolami dostępne z poziomu panelu admina Django


### US-03 — Ograniczenie dostępu prawnika do własnych spraw

**Jako** prawnik  
**chcę** widzieć i edytować wyłącznie sprawy, do których jestem przypisany (via `CaseLawyer`),  
**aby** zachowana była poufność danych między prawnikami.

**Kryteria akceptacji:**
- [ ] Queryset spraw filtrowany po zalogowanym użytkowniku (o ile nie jest adminem)
- [ ] Próba bezpośredniego dostępu do cudzej sprawy przez URL zwraca 403 lub 404
- [ ] Administrator widzi wszystkie sprawy
- [ ] Filtr nie dotyczy panelu `/admin/`

---

### US-04 — Klienci

**Jako** pracownik **chcę** dodawać, przeglądać i edytować klientów,
**aby** rejestrować kontrahentów kancelarii.

- [ ] Formularz z walidacją `clean()`: osoba fizyczna wymaga PESEL, firma wymaga NIP
- [ ] Błąd walidacji wyświetlany pod polem
- [ ] Usunięcie zablokowane (`RESTRICT`), gdy klient ma aktywne sprawy
- [ ] Wyszukiwanie klienta po nazwisku lub nazwie firmy

---

### US-05 — Sprawy (CRUD + filtrowanie)

**Jako** prawnik **chcę** tworzyć, przeglądać, edytować i wyszukiwać sprawy,
**aby** zarządzać zleceniami kancelarii.

- [ ] Tworzenie sprawy: unikalny `case_number`, status domyślnie `nowa`
- [ ] Lista z filtrem (status / typ) i paginacją (20/stronę) lub sortowaniem
- [ ] Wyszukiwanie po `case_number`, sygnaturze sądowej lub nazwisku klienta
- [ ] Edycja: zmiana statusu na `zakończona` ustawia `closed_at`
- [ ] Tworzenie sprawy aytomatycznie przypisuje prawnika jako `prowadzący`

---

### US-06 — Terminy sądowe

**Jako** prawnik **chcę** dodawać terminy sądowe do sprawy i zmieniać ich status,
**aby** śledzić kalendarz procesowy.

- [ ] Walidacja: data terminu musi być w przyszłości (dla nowych rekordów)
- [ ] Status domyślnie `planowany`; zmiana na odbyty / odroczony / odwołany
- [ ] Termin widoczny na stronie szczegółowej sprawy
- [ ] Domyślne wyprzedzenie przypomnienia: 1440 minut (24 h)

---

### US-07 — Faktury

**Jako** pracownik  
**chcę** wystawiać faktury powiązane ze sprawą, z automatycznym wyliczeniem kwoty brutto, i zmieniać ich status 
**aby** rozliczać usługi kancelarii bez ręcznego przeliczania VAT.

**Kryteria akceptacji:**
- [ ] `gross_amount = net_amount × (1 + vat_rate)` wyliczane w metodzie `save()`
- [ ] Unikalny numer faktury (`invoice_number`)
- [ ] Status domyślnie ustawiony na `wystawiona`
- [ ] Waluta domyślnie `PLN

---

### US-08 — Zadania

**Jako** prawnik **chcę** tworzyć zadania przypisane do prawnika i zmieniać ich status,
**aby** organizować bieżącą pracę.

- [ ] Status domyślnie `nowe`; zmiana na `zakończone` ustawia `completed_at`
- [ ] Widok „moje zadania" filtruje po zalogowanym prawniku
- [ ] Priorytet wybierany z listy (niska / normalna / wysoka / pilna)
- [ ] Pole `parent_task` opcjonalne — umożliwia tworzenie podzadań
- [ ] Zadanie może istnieć bez przypisanej sprawy
- [ ] Widok „moje zadania" wyświetla zadania przypisane do zalogowanego prawnika
- [ ] Filtry: status, priorytet
- [ ] Sortowanie po `due_date` (rosnąco)
- [ ] Zadania przeterminowane wyróżnione wizualnie

---

### US-09 — Dodawanie dokumentów i wgrywanie wersji

**Jako** prawnik  
**chcę** dodawać dokumenty do sprawy i wgrywać ich wersje (pliki),  
**aby** archiwizować pisma, umowy i dowody w jednym miejscu.

**Kryteria akceptacji:**
- [ ] Upload pliku zapisuje ścieżkę w polu `file_path` modelu `DocumentVersion`
- [ ] Numer wersji (`version_number`) inkrementowany automatycznie
- [ ] Typ dokumentu wybierany z listy enum (pozew, odpowiedź, notatka itd.)
- [ ] Dokument widoczny na stronie szczegółowej sprawy

---

### Cykl życia sprawy

**Jako** prawnik **chcę** obsłużyć sprawę od przyjęcia do zamknięcia w jednym widoku,
**aby** nie przełączać się między ekranami.

- [ ] Widok `case_detail` agreguje: przypisania prawników, terminy, dokumenty, zadania, faktury
- [ ] Zmiana statusu dostępna bezpośrednio z widoku szczegółowego
- [ ] Akcja „Zamknij sprawę" → status `zakończona` + link do nowej faktury z pre-wypełnionym `case`
- [ ] Każda sekcja zawiera skrót do dodania nowego rekordu (termin, dokument, zadanie, faktura)
- [ ] Historia zmian statusu widoczna (pole `updated_at` + status)

---
