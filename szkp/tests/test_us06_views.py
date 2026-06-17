from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from szkp.models import (
    Case, CaseType, CourtHearing, HearingStatus, HearingType,
)
from szkp.tests.base import StaffLawyerTestCase


@tag('integration')
class CourtHearingCreateViewTest(StaffLawyerTestCase):
    """court_hearing_form (nowy termin): walidacja POST, tworzenie, domyślne wartości."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US06-001',
            title='Sprawa do testów terminów', case_type=CaseType.CYWILNA,
        )

    def _url_new(self):
        return reverse('szkp:court_hearing_new', kwargs={'case_pk': self.sprawa.pk})

    def _valid_data(self, **overrides):
        data = {
            'court_name': 'Sąd Rejonowy w Krakowie',
            'hearing_type': HearingType.ROZPRAWA,
            'scheduled_at': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M'),
            'reminder_minutes_before': 1440,
        }
        data.update(overrides)
        return data

    def test_get_formularz_zwraca_200(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 200)

    def test_domyslne_przypomnienie_w_formularzu(self):
        r = self.client.get(self._url_new())
        self.assertEqual(r.context['form']['reminder_minutes_before'].value(), 1440)

    def test_post_z_data_przyszla_tworzy_termin(self):
        self.client.post(self._url_new(), self._valid_data())
        self.assertTrue(
            CourtHearing.objects.filter(
                case=self.sprawa, court_name='Sąd Rejonowy w Krakowie',
            ).exists()
        )

    def test_nowy_termin_ma_status_planowany(self):
        self.client.post(self._url_new(), self._valid_data(court_name='Sąd Okręgowy w Łodzi'))
        termin = CourtHearing.objects.get(court_name='Sąd Okręgowy w Łodzi')
        self.assertEqual(termin.status, HearingStatus.PLANOWANY)

    def test_post_z_data_przeszla_zwraca_blad(self):
        przeszla = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        r = self.client.post(self._url_new(), self._valid_data(scheduled_at=przeszla))
        self.assertEqual(r.status_code, 200)
        self.assertIn('scheduled_at', r.context['form'].errors)

    def test_po_zapisie_redirect_do_szczegolów_sprawy(self):
        r = self.client.post(self._url_new(), self._valid_data())
        self.assertRedirects(
            r,
            reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=terminy',
        )

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_us06', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url_new())
        self.assertEqual(r.status_code, 403)


@tag('integration')
class CourtHearingEditViewTest(StaffLawyerTestCase):
    """court_hearing_form (edycja terminu): aktualizacja statusu, brak walidacji daty."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-US06-EDIT-001',
            title='Sprawa do edycji terminów', case_type=CaseType.CYWILNA,
        )
        cls.termin = CourtHearing.objects.create(
            case=cls.sprawa,
            court_name='Sąd Rejonowy w Poznaniu',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=datetime.now(tz=timezone.utc) + timedelta(days=5),
            status=HearingStatus.PLANOWANY,
        )

    def _url_edit(self):
        return reverse(
            'szkp:court_hearing_edit',
            kwargs={'case_pk': self.sprawa.pk, 'pk': self.termin.pk},
        )

    def _valid_edit_data(self, **overrides):
        data = {
            'court_name': self.termin.court_name,
            'hearing_type': self.termin.hearing_type,
            'scheduled_at': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'status': HearingStatus.PLANOWANY,
            'reminder_minutes_before': 1440,
        }
        data.update(overrides)
        return data

    def test_get_formularz_edycji_zwraca_200(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 200)

    def test_get_formularz_zawiera_dane_terminu(self):
        r = self.client.get(self._url_edit())
        self.assertEqual(r.context['form']['court_name'].value(), self.termin.court_name)

    def test_post_zmienia_status_na_odbyty(self):
        self.client.post(self._url_edit(), self._valid_edit_data(status='odbyty'))
        self.termin.refresh_from_db()
        self.assertEqual(self.termin.status, HearingStatus.ODBYTY)

    def test_edycja_pozwala_na_date_w_przeszlosci(self):
        przeszla = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        r = self.client.post(self._url_edit(), self._valid_edit_data(scheduled_at=przeszla))
        self.assertEqual(r.status_code, 302)

    def test_po_edycji_redirect_do_szczegolów_sprawy(self):
        r = self.client.post(self._url_edit(), self._valid_edit_data())
        self.assertRedirects(
            r,
            reverse('szkp:case_detail', kwargs={'pk': self.sprawa.pk}) + '?tab=terminy',
        )

    def test_wymaga_zalogowania(self):
        self.client.logout()
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/', r['Location'])

    def test_nieprzypisany_prawnik_dostaje_403(self):
        user2 = User.objects.create_user('obcy_us06_edit', password='pass', is_staff=False)
        self.client.force_login(user2)
        r = self.client.get(self._url_edit())
        self.assertEqual(r.status_code, 403)
