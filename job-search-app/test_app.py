import io
import unittest
from pathlib import Path
from resume import read_document,extract

class ResumeTests(unittest.TestCase):
    def test_text(self):
        p=extract(read_document('r.txt',b'UMKC\nChicago, IL\nSQL Python'),['SQL','Python','R'])
        self.assertEqual(p['skills'],'SQL, Python')
        self.assertEqual(p['location'],'Chicago, IL')
        self.assertIn('SQL',p['evidence']['SQL']['Evidence'])
    def test_docx(self):
        from docx import Document
        doc=Document(); doc.add_paragraph('SQL at UMKC'); b=io.BytesIO(); doc.save(b)
        self.assertIn('SQL',read_document('r.docx',b.getvalue())[0][1])
    def test_size_limit(self):
        with self.assertRaises(ValueError): read_document('r.txt',b'x'*(5*1024*1024+1))
    def test_ui(self):
        from streamlit.testing.v1 import AppTest
        a=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=30)
        self.assertFalse(a.exception)
        a.text_area[0].set_value('UMKC\nChicago, IL\nSQL Python Excel')
        next(b for b in a.button if b.label=='Extract profile').click().run(timeout=30)
        self.assertFalse(a.exception)
        next(b for b in a.button if b.label=='Search Jobs').click().run(timeout=30)
        self.assertFalse(a.exception)
        self.assertEqual(len(a.metric),1)
        self.assertEqual(len(a.session_state['results']),5)
        self.assertTrue(all(r['scores']['Skills'] is not None for r in a.session_state['results']))
        next(b for b in a.button if b.label=='Confirm decision').click().run(timeout=30)
        self.assertFalse(a.exception)
        self.assertTrue(a.session_state['feedback'])

if __name__=='__main__': unittest.main()
