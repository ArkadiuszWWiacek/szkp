from django.test import SimpleTestCase, tag

from szkp.models import Document, DocumentVersion


@tag('unit')
class DocumentStrTest(SimpleTestCase):
    def test_str(self):
        doc = Document(title='Pozew o zapłatę')
        self.assertEqual(str(doc), 'Pozew o zapłatę')


@tag('unit')
class DocumentVersionStrTest(SimpleTestCase):
    def test_str(self):
        doc = Document(title='Pozew o zapłatę')
        version = DocumentVersion(document=doc, version_number=2)
        self.assertEqual(str(version), 'Pozew o zapłatę v2')
