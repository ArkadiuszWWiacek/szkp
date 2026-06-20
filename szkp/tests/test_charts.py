import base64

from django.test import SimpleTestCase, tag

from szkp.charts import generate_case_dist_chart


@tag('unit')
class GenerateCaseDistChartTest(SimpleTestCase):

    def test_returns_nonempty_string_with_data(self):
        cases_by_status = {'w_toku': 5, 'nowa': 3, 'zawieszona': 1, 'zakończona': 8}
        result = generate_case_dist_chart(cases_by_status, 17)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_returns_empty_string_when_total_zero(self):
        result = generate_case_dist_chart({}, 0)
        self.assertEqual(result, '')

    def test_result_is_valid_base64(self):
        cases_by_status = {'w_toku': 5, 'nowa': 3}
        result = generate_case_dist_chart(cases_by_status, 8)
        decoded = base64.b64decode(result)
        self.assertGreater(len(decoded), 0)

    def test_handles_partial_statuses(self):
        result = generate_case_dist_chart({'w_toku': 5, 'zakończona': 2}, 7)
        self.assertGreater(len(result), 0)

    def test_handles_single_status(self):
        result = generate_case_dist_chart({'zakończona': 10}, 10)
        self.assertGreater(len(result), 0)
