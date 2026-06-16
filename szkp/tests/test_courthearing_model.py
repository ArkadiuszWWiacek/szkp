from datetime import datetime, timezone

from django.test import SimpleTestCase, TestCase, tag

from szkp.models import Case, CaseType, Client, ClientType, CourtHearing, HearingStatus, HearingType


@tag('unit')
class CourtHearingDefaultsTest(SimpleTestCase):
    def test_domyslny_status_planowany(self):
        self.assertEqual(CourtHearing().status, HearingStatus.PLANOWANY)

    def test_domyslne_przypomnienie_1440(self):
        self.assertEqual(CourtHearing().reminder_minutes_before, 1440)

    def test_responsible_lawyer_moze_byc_pusty(self):
        self.assertIsNone(CourtHearing().responsible_lawyer)


@tag('unit')
class CourtHearingStrTest(SimpleTestCase):
    def test_str(self):
        case = Case(case_number='1/2024/CIV', title='Sprawa testowa')
        hearing = CourtHearing(
            case=case,
            scheduled_at=datetime(2024, 5, 15, 10, 0, tzinfo=timezone.utc),
            court_name='Sąd Okręgowy w Warszawie',
        )
        self.assertEqual(str(hearing), '1/2024/CIV - Sprawa testowa / 2024-05-15 / Sąd Okręgowy w Warszawie')


@tag('integration')
class CourtHearingPersistenceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA,
            first_name='Jan', last_name='Testowy', pesel='89010112345',
        )

    def _przyszla_data(self):
        from datetime import timedelta
        return datetime.now(tz=timezone.utc) + timedelta(days=7)

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
