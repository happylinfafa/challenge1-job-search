import unittest
import pandas as pd
from matching import rank_jobs

class MatchingTests(unittest.TestCase):
    def job(self,**updates):
        x=dict(job_id='A',skills='Python; SQL; Tableau; Excel',salary_min=70000,salary_max=90000,location='Chicago, IL',company_size='51 to 200 employees')
        x.update(updates); return x
    def rank(self,*rows):
        return rank_jobs(pd.DataFrame(rows),'python, SQL, Excel','Chicago,IL',80000,'51 to 200 employees')
    def test_manual_score(self):
        self.assertEqual(self.rank(self.job())[0]['score'],75.0)
    def test_missing_reweight(self):
        r=self.rank(self.job(company_size=None))[0]
        self.assertAlmostEqual(r['score'],55/.8)
        self.assertIsNone(r['scores']['Size'])
    def test_no_skill_evidence(self):
        self.assertIsNone(self.rank(self.job(skills=None))[0]['scores']['Skills'])
    def test_remote_not_inferred(self):
        self.assertEqual(self.rank(self.job(location='Remote'))[0]['scores']['Location'],0)
    def test_salary_boundaries(self):
        self.assertEqual(self.rank(self.job(salary_min=80000))[0]['scores']['Salary'],100)
        self.assertEqual(self.rank(self.job(salary_max=79999))[0]['scores']['Salary'],0)
    def test_order(self):
        r=self.rank(self.job(job_id='B'),self.job(job_id='A'),self.job(job_id='C',salary_min=80000))
        self.assertEqual([x['job']['job_id'] for x in r],['C','A','B'])

if __name__=='__main__': unittest.main()
