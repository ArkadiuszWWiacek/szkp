from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from szkp.models import Case, CaseType, Lawyer, Task, TaskPriority, TaskStatus
from szkp.tests.base import StaffLawyerTestCase
from szkp.tests.utils import make_due


@tag('integration')
class MyTasksViewTest(StaffLawyerTestCase):
    """my_tasks view: dostępność, filtry, sortowanie."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US08-001',
            title='Sprawa do testów zadań', case_type=CaseType.CYWILNA,
        )

    def _url(self):
        return reverse('szkp:my_tasks')

    def _make_task(self, **kwargs):
        return Task.objects.create(
            assigned_lawyer=self.lawyer, created_by=self.lawyer, **kwargs
        )

    def test_get_zwraca_200(self):
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 200)

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_kontekst_zawiera_wymagane_klucze(self):
        r = self.client.get(self._url())
        for key in ('tasks', 'status_filter', 'period_filter', 'status_choices', 'today'):
            self.assertIn(key, r.context)

    def test_wyswietla_tylko_zadania_top_level(self):
        parent = self._make_task(title='Rodzic')
        child = self._make_task(title='Dziecko', parent_task=parent)
        r = self.client.get(self._url())
        pks = [t.pk for t in r.context['tasks']]
        self.assertIn(parent.pk, pks)
        self.assertNotIn(child.pk, pks)

    def test_filtr_statusu_ogranicza_wyniki(self):
        t_nowe = self._make_task(title='Zadanie nowe', status=TaskStatus.NOWE)
        t_zakonczone = self._make_task(title='Zadanie zakończone', status=TaskStatus.ZAKOŃCZONE)
        r = self.client.get(self._url() + '?status=nowe')
        pks = [t.pk for t in r.context['tasks']]
        self.assertIn(t_nowe.pk, pks)
        self.assertNotIn(t_zakonczone.pk, pks)

    def test_filtr_period_today(self):
        t_dzis = self._make_task(title='Na dziś', due_date=make_due(0))
        t_tydzien = self._make_task(title='Za tydzień', due_date=make_due(7))
        r = self.client.get(self._url() + '?period=today')
        pks = [t.pk for t in r.context['tasks']]
        self.assertIn(t_dzis.pk, pks)
        self.assertNotIn(t_tydzien.pk, pks)

    def test_filtr_period_week(self):
        t_za_3_dni = self._make_task(title='Za 3 dni', due_date=make_due(3))
        t_za_14_dni = self._make_task(title='Za 14 dni', due_date=make_due(14))
        r = self.client.get(self._url() + '?period=week')
        pks = [t.pk for t in r.context['tasks']]
        self.assertIn(t_za_3_dni.pk, pks)
        self.assertNotIn(t_za_14_dni.pk, pks)

    def test_sortowanie_priorytet_pilna_przed_niska(self):
        t_niska = self._make_task(title='Niska', priority=TaskPriority.NISKA, due_date=make_due(1))
        t_pilna = self._make_task(title='Pilna', priority=TaskPriority.PILNA, due_date=make_due(5))
        r = self.client.get(self._url())
        pks = [t.pk for t in r.context['tasks']]
        self.assertLess(pks.index(t_pilna.pk), pks.index(t_niska.pk))

    # --- filtrowanie po zalogowanym prawniku (RED — brak filtra) ---

    def test_widok_filtruje_po_zalogowanym_prawniku(self):
        inny_user = User.objects.create_user(username='innyprawnik', password='pass')
        inny_prawnik = Lawyer.objects.create(
            user=inny_user, first_name='Inna', last_name='Osoba', bar_number='PL999',
        )
        Task.objects.create(
            title='Zadanie innego prawnika',
            assigned_lawyer=inny_prawnik,
            created_by=inny_prawnik,
        )
        r = self.client.get(self._url())
        pks = [t.pk for t in r.context['tasks']]
        self.assertFalse(
            Task.objects.filter(title='Zadanie innego prawnika', pk__in=pks).exists()
        )


@tag('integration')
class TaskCreateViewTest(StaffLawyerTestCase):
    """task_form (nowe zadanie): walidacja, tworzenie, domyślne wartości.
    RED — URL szkp:task_new nie istnieje."""

    def _url_new(self):
        return reverse('szkp:task_new')

    def _valid_data(self, **overrides):
        data = {'title': 'Nowe zadanie', 'priority': 'normalna'}
        data.update(overrides)
        return data

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 200)

    def test_post_tworzy_zadanie(self):
        self.client.post(self._url_new(), self._valid_data())
        self.assertTrue(Task.objects.filter(title='Nowe zadanie').exists())

    def test_nowe_zadanie_ma_status_nowe(self):
        self.client.post(self._url_new(), self._valid_data(title='Zadanie statusowe'))
        task = Task.objects.get(title='Zadanie statusowe')
        self.assertEqual(task.status, TaskStatus.NOWE)

    def test_priorytet_ustawiany_z_formularza(self):
        self.client.post(self._url_new(), self._valid_data(title='Pilne', priority='pilna'))
        task = Task.objects.get(title='Pilne')
        self.assertEqual(task.priority, TaskPriority.PILNA)

    def test_brak_tytulu_zwraca_blad(self):
        r = self.client.post(self._url_new(), {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['errors'])

    def test_po_zapisie_redirect_do_listy_zadan(self):
        r = self.client.post(self._url_new(), self._valid_data())
        self.assertRedirects(r, reverse('szkp:my_tasks'))

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])


@tag('integration')
class TaskEditViewTest(StaffLawyerTestCase):
    """task_form (edycja zadania): zmiana statusu, completed_at.
    RED — URL szkp:task_edit nie istnieje."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.zadanie = Task.objects.create(
            title='Zadanie do edycji',
            assigned_lawyer=cls.lawyer,
            created_by=cls.lawyer,
        )

    def _url_edit(self):
        return reverse('szkp:task_edit', kwargs={'pk': self.zadanie.pk})

    def _valid_edit_data(self, **overrides):
        data = {
            'title': self.zadanie.title,
            'priority': self.zadanie.priority,
            'status': self.zadanie.status,
        }
        data.update(overrides)
        return data

    def test_get_formularz_edycji_zwraca_200(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 200)

    def test_get_formularz_zawiera_dane_zadania(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.context['form_data']['title'], self.zadanie.title)

    def test_post_zmienia_status_na_zakonczone(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='zakończone'))
        self.zadanie.refresh_from_db()
        self.assertEqual(self.zadanie.status, TaskStatus.ZAKOŃCZONE)

    def test_zakonczenie_zadania_ustawia_completed_at(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='zakończone'))
        self.zadanie.refresh_from_db()
        self.assertIsNotNone(self.zadanie.completed_at)

    def test_po_edycji_redirect_do_listy_zadan(self):
        r = self.client.post(self._url_edit(), self._valid_edit_data())
        self.assertRedirects(r, reverse('szkp:my_tasks'))

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])
