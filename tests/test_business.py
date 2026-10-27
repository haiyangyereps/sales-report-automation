import tempfile,unittest
from pathlib import Path
from business import analyze,html
class BusinessTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)/'orders.csv'
 def tearDown(self):self.t.cleanup()
 def source(self,rows):self.p.write_text('event_id,order_id,date,kind,amount,cost,fee,channel,currency\n'+rows);return self.p
 def test_margin_detects_unprofitable_channel(self):
  r=analyze(Path(__file__).resolve().parents[1]/'examples/orders.csv');self.assertEqual(r['totals']['net'],'540.00');self.assertEqual(r['totals']['contribution'],'238.00');self.assertEqual(r['channels']['marketplace']['contribution'],'-47.00');self.assertEqual(r['alerts'][0]['channel'],'marketplace');self.assertEqual(r['average_order_value'],'200.00')
 def test_refund_reference_validation(self):
  sale='a,o1,2026-10-01,sale,100,20,3,web,USD\n'
  for refund in ('r,o2,2026-10-02,refund,20,0,0,web,USD\n','r,o1,2026-10-02,refund,101,0,0,web,USD\n','r,o1,2026-09-30,refund,20,0,0,web,USD\n','r,o1,2026-10-02,refund,20,0,0,other,USD\n'):
   self.assertEqual(analyze(self.source(sale+refund))['status'],'invalid')
 def test_multiple_partial_refunds(self):
  r=analyze(self.source('a,o1,2026-10-01,sale,100,20,3,web,USD\nr1,o1,2026-10-02,refund,20,0,0,web,USD\nr2,o1,2026-10-03,refund,30,0,0,web,USD\n'));self.assertEqual(r['totals']['net'],'50.00')
 def test_html_escapes_untrusted_channel(self):
  r=analyze(self.source('a,o1,2026-10-01,sale,100,20,3,<script>,USD\n'));self.assertIn('&lt;script&gt;',html(r));self.assertNotIn('<script>',html(r))
 def test_rejects_ambiguous_currency_and_duplicate_sale(self):
  a='a,o1,2026-10-01,sale,100,20,3,web,USD\n'
  for b in ('b,o2,2026-10-01,sale,100,20,3,web,EUR\n','b,o1,2026-10-01,sale,100,20,3,web,USD\n'):
   self.assertEqual(analyze(self.source(a+b))['status'],'invalid')
if __name__=='__main__':unittest.main()
