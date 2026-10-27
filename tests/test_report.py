import unittest,tempfile
from pathlib import Path
from report import analyze,write_report,render
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def source(self,rows):
  p=self.root/'sales.csv';p.write_text('transaction_id,date,amount,currency\n'+rows);return p
 def test_metrics_and_missing_dates(self):
  r=analyze(self.source('a,2026-10-01,200,USD\nb,2026-10-03,300,USD\nc,2026-10-03,-20,USD\n'))
  self.assertEqual(r['net'],'480');self.assertEqual(r['gross'],'500');self.assertEqual(r['average_positive_sale'],'250.00');self.assertEqual(r['daily']['2026-10-02'],'0');self.assertEqual(r['refund_value_rate'],'4.00')
 def test_invalid_rows_no_partial_report(self):
  for rows in ['a,2026-10-01,NaN,USD\n','a,2026-10-01,1,USD\na,2026-10-01,2,USD\n','a,2026-10-01,1,USD\nb,2026-10-02,1,EUR\n','a,2026-02-30,1,USD\n','a,2026-10-01,1.001,USD\n']:
   p=self.source(rows);out=self.root/'out.html';self.assertEqual(write_report(p,out)['status'],'invalid');self.assertFalse(out.exists())
 def test_failed_report_preserves_previous_output(self):
  out=self.root/'report.html';out.write_text('previous');write_report(self.source('a,2026-10-01,NaN,USD\n'),out);self.assertEqual(out.read_text(),'previous')
 def test_refund_only(self):
  r=analyze(self.source('a,2026-10-01,-20,USD\n'));self.assertIsNone(r['refund_value_rate']);self.assertIn('#c24145',render(r))
 def test_complete_html(self):
  out=self.root/'report.html';write_report(self.source('a,2026-10-01,2.50,USD\n'),out);self.assertIn('2.50',out.read_text());self.assertIn('Daily net sales',out.read_text())
if __name__=='__main__':unittest.main()
