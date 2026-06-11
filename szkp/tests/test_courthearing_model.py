from datetime import datetime, timezone

from django.test import TestCase, tag

from szkp.models import Case, CaseType, Client, ClientType, CourtHearing, HearingStatus, HearingType


@tag('unit')
class CourtHearingModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Testowy', pesel='89010112345',
        )
        cls.sprawa = Case.objects.create(
            client=cls.klient, case_number='TST-CH-001',
            title='Sprawa do testów terminów', case_type=CaseType.CYWILNA,
        )

    def _przyszla_data(self):
        from datetime import timedelta
        return datetime.now(tz=timezone.utc) + timedelta(days=7)

    def test_domyslny_status_planowany(self):
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Rejonowy w Krakowie',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=self._przyszla_data(),
        )
        self.assertEqual(termin.status, HearingStatus.PLANOWANY)

    def test_domyslne_przypomnienie_1440(self):
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Rejonowy w Krakowie',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=self._przyszla_data(),
        )
        self.assertEqual(termin.reminder_minutes_before, 1440)

    def test_responsible_lawyer_moze_byc_pusty(self):
        termin = CourtHearing.objects.create(
            case=self.sprawa,
            court_name='Sąd Okręgowy w Warszawie',
            hearing_type=HearingType.POSIEDZENIE,
            scheduled_at=self._przyszla_data(),
        )
        self.assertIsNone(termin.responsible_lawyer)

    def test_usuniecie_sprawy_kaskaduje_na_termin(self):
        sprawa = Case.objects.create(
            client=self.klient, case_number='TST-CH-CASCADE',
            title='Sprawa do usunięcia', case_type=CaseType.CYWILNA,
        )
        termin = CourtHearing.objects.create(
            case=sprawa,
            court_name='Sąd Apelacyjny w Gdańsku',
            hearing_type=HearingType.ROZPRAWA,
            scheduled_at=self._przyszla_data(),
        )
        pk = termin.pk
        sprawa.delete()
        self.assertFalse(CourtHearing.objects.filter(pk=pk).exists())
