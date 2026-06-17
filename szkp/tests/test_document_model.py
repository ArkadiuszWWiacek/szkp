from django.test import SimpleTestCase, tag

from szkp.models import Document, DocumentVersion


@tag('unit')
class DocumentStrTest(SimpleTestCase):
    """Document.__str__: zwraca tytuł dokumentu."""

    def test_str(self):
        """str(Document) zwraca tytuł dokumentu."""
        doc = Document(title='Pozew o zapłatę')
        self.assertEqual(str(doc), 'Pozew o zapłatę')


@tag('unit')
class DocumentVersionStrTest(SimpleTestCase):
    """DocumentVersion.__str__: format 'tytuł vN'."""

    def test_str(self):
        """str(DocumentVersion) zwraca 'tytuł vN'."""
        doc = Document(title='Pozew o zapłatę')
        version = DocumentVersion(document=doc, version_number=2)
        self.assertEqual(str(version), 'Pozew o zapłatę v2')
