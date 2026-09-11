import unittest
from eligibility import classify
class FilterTests(unittest.TestCase):
    def check(self,**kw):
        row=dict(job_id='TEST',salary_min=60000,salary_max=90000,salary_currency='USD',salary_period='annual_assumed',location='Remote')
        row.update(kw)
        return classify(row)['eligible']
    def test_inclusive(self): self.assertTrue(self.check())
    def test_below(self): self.assertFalse(self.check(salary_min=59999))
    def test_above(self): self.assertTrue(self.check(salary_min=60001))
    def test_missing(self): self.assertFalse(self.check(salary_min=None))
    def test_invalid(self): self.assertFalse(self.check(salary_max=50000))
    def test_currency(self): self.assertFalse(self.check(salary_currency='EUR'))
    def test_hourly(self): self.assertFalse(self.check(salary_period='hourly'))
    def test_location_not_filter(self): self.assertTrue(self.check(location='Toronto, ON'))
if __name__=='__main__': unittest.main()
