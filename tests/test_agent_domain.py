import tempfile,unittest
from pathlib import Path
from agent import configure
from agent_runtime import Journal
class DomainTests(unittest.TestCase):
 def test_unknown_channel_cannot_create_task(self):
  with tempfile.TemporaryDirectory() as d:
   j=Journal(str(Path(d)/'j.db'));_,h,_=configure('examples/orders.csv',j)
   with self.assertRaises(ValueError):h['propose_review_task']({'channel':'invented','recommendation':'change prices'},'r')
   self.assertEqual(j.db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0],0)
 def test_invalid_data_blocks_agent_setup(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.csv';p.write_text('event_id,order_id,date,kind,amount,cost,fee,channel,currency\nbad,o1,2026-01-01,sale,-1,0,0,web,USD\n')
   with self.assertRaises(ValueError):configure(str(p),Journal(str(Path(d)/'j.db')))
