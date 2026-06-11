from django.contrib.auth.models import User
from django.test import TestCase, tag

from szkp.models import (
    Case, CaseType,
    CaseLawyer, CaseLawyerRole,
    Client, ClientType,
    Lawyer,
)


class _US03SetUpMixin:
    def setUp(self):
        self.lawyer_a = Lawyer.objects.create(
            first_name='Andrzej', last_name='Adamski', bar_number='TST/A/001'
        )
        self.user_a = User.objects.create_user(username='andrzej_adamski', password='x')
        self.lawyer_a.user = self.user_a
        self.lawyer_a.save()

        self.lawyer_b = Lawyer.objects.create(
            first_name='Barbara', last_name='Bogacka', bar_number='TST/B/001'
        )
        self.user_b = User.objects.create_user(username='barbara_bogacka', password='x')
        self.lawyer_b.user = self.user_b
        self.lawyer_b.save()

        self.admin = User.objects.create_user(
            username='admin_test', password='x', is_staff=True, is_superuser=True
        )

        klient = Client.objects.create(
            type=ClientType.OSOBA_FIZYCZNA, pesel='12345678901'
        )
        self.case_a = Case.objects.create(
            client=klient, case_number='TST-A-001',
            title='Sprawa Adwokata A', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.case_a, lawyer=self.lawyer_a, role=CaseLawyerRole.PROWADZACY
        )
        self.case_b = Case.objects.create(
            client=klient, case_number='TST-B-001',
            title='Sprawa Adwokata B', case_type=CaseType.CYWILNA,
        )
        CaseLawyer.objects.create(
            case=self.case_b, lawyer=self.lawyer_b, role=CaseLawyerRole.PROWADZACY
        )


@tag('integration')
class CaseListAccessTest(_US03SetUpMixin, TestCase):
    """US-03: filtrowanie listy spraw po zalogowanym prawniku."""

    def test_case_list_zwraca_200(self):
        self.client.force_login(self.user_a)
        response = self.client.get('/szkp/sprawy/')
        self.assertEqual(response.status_code, 200)

    def test_prawnik_widzi_tylko_swoje_sprawy(self):
        self.client.force_login(self.user_a)
        response = self.client.get('/szkp/sprawy/')
        cases = list(response.context['page_obj'])
        self.assertIn(self.case_a, cases)
        self.assertNotIn(self.case_b, cases)

    def test_admin_widzi_wszystkie_sprawy(self):
        self.client.force_login(self.admin)
        response = self.client.get('/szkp/sprawy/')
        cases = list(response.context['page_obj'])
        self.assertIn(self.case_a, cases)
        self.assertIn(self.case_b, cases)


@tag('integration')
class CaseDetailAccessTest(_US03SetUpMixin, TestCase):
    """US-03: kontrola dostępu do szczegółu sprawy."""

    def test_przypisany_prawnik_ma_dostep(self):
        self.client.force_login(self.user_a)
        response = self.client.get(f'/szkp/sprawy/{self.case_a.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_nieprzypisany_prawnik_jest_blokowany(self):
        self.client.force_login(self.user_a)
        response = self.client.get(f'/szkp/sprawy/{self.case_b.pk}/')
        self.assertNotEqual(response.status_code, 200)  # 302 / 403 / 404

    def test_admin_ma_dostep_do_kazdej_sprawy(self):
        self.client.force_login(self.admin)
        response = self.client.get(f'/szkp/sprawy/{self.case_b.pk}/')
        self.assertEqual(response.status_code, 200)
