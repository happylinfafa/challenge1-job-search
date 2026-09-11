import io
import unittest
from pathlib import Path
from resume import read_document,extract

class ResumeTests(unittest.TestCase):
    def setUp(self):
        import streamlit as st
        st.cache_data.clear()
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
        next(n for n in a.number_input if n.label=='Skills weight (%)').set_value(55)
        next(b for b in a.button if b.label=='Search Jobs').click().run(timeout=30)
        self.assertTrue(a.error)
        self.assertNotIn('results',a.session_state)

    def test_empty_results(self):
        from unittest.mock import patch
        import pandas as pd
        from streamlit.testing.v1 import AppTest
        import eligibility
        original=eligibility.screen
        def empty(jobs):
            _,audit=original(jobs)
            return jobs.iloc[:0].copy(),audit
        with patch('eligibility.screen',side_effect=empty):
            a=AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=30)
            a.text_input(key='skills').set_value('SQL')
            a.text_input(key='location').set_value('Chicago, IL')
            next(b for b in a.button if b.label=='Search Jobs').click().run(timeout=30)
            self.assertFalse(a.exception)
            self.assertEqual(len(a.session_state['results']),0)

if __name__=='__main__': unittest.main()
