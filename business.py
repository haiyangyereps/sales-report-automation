"""Order-level contribution analysis with channel attribution and refund reconciliation."""
import argparse,csv,json
from collections import defaultdict
from decimal import Decimal,InvalidOperation
from datetime import date
from html import escape
from pathlib import Path
from report import render

def amount(text):
 try:
  n=Decimal(text)
  if not n.is_finite() or n<0 or n>Decimal('100000000') or n!=n.quantize(Decimal('.01')):raise ValueError('invalid non-negative currency amount')
  return n
 except (InvalidOperation,TypeError):raise ValueError('invalid currency amount')

def analyze(source):
 orders={};refunds=[];events=set();currencies=set();errors=[]
 with open(source,newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  required={'event_id','order_id','date','kind','amount','cost','fee','channel','currency'}
  if not required<=set(reader.fieldnames or []):raise ValueError('missing columns: '+','.join(sorted(required-set(reader.fieldnames or []))))
  for line,r in enumerate(reader,2):
   try:
    eid=r['event_id'].strip();oid=r['order_id'].strip();channel=r['channel'].strip();kind=r['kind']
    if not eid or not oid or not channel:raise ValueError('event, order, channel required')
    if eid in events:raise ValueError('duplicate event ID')
    day=date.fromisoformat(r['date']);value=amount(r['amount']);cost=amount(r['cost']);fee=amount(r['fee']);currency=r['currency'].strip().upper()
    if len(currency)!=3 or not currency.isascii() or not currency.isalpha():raise ValueError('invalid currency code')
    if kind not in ('sale','refund'):raise ValueError('kind must be sale or refund')
    if kind=='sale' and oid in orders:raise ValueError('one sale row per order required')
    if kind=='refund' and cost:raise ValueError('refund cost must be zero; returned inventory recovery is outside scope')
    events.add(eid);currencies.add(currency);entry={'line':line,'id':oid,'day':day.isoformat(),'amount':value,'cost':cost,'fee':fee,'channel':channel}
    if kind=='sale':orders[oid]=entry
    else:refunds.append(entry)
   except (ValueError,AttributeError) as exc:errors.append({'line':line,'reason':str(exc)})
 if len(currencies)>1:errors.append({'line':0,'reason':'mixed currencies'})
 if not orders:errors.append({'line':0,'reason':'no sale orders'})
 refunded=defaultdict(Decimal)
 for r in refunds:
  o=orders.get(r['id'])
  if not o:errors.append({'line':r['line'],'reason':'refund references unknown order'});continue
  if r['channel']!=o['channel'] or r['day']<o['day']:errors.append({'line':r['line'],'reason':'refund channel/date conflicts with sale'})
  refunded[r['id']]+=r['amount']
  if refunded[r['id']]>o['amount']:errors.append({'line':r['line'],'reason':'refund exceeds original sale'})
 if errors:return {'status':'invalid','errors':errors}
 channels={};daily=defaultdict(Decimal)
 for o in orders.values():
  m=channels.setdefault(o['channel'],{'orders':0,'gross':Decimal(0),'refunds':Decimal(0),'cost':Decimal(0),'fees':Decimal(0)})
  m['orders']+=1;m['gross']+=o['amount'];m['cost']+=o['cost'];m['fees']+=o['fee'];daily[o['day']]+=o['amount']
 for r in refunds:channels[r['channel']]['refunds']+=r['amount'];channels[r['channel']]['fees']+=r['fee'];daily[r['day']]-=r['amount']
 for m in channels.values():
  m['net']=m['gross']-m['refunds'];m['contribution']=m['net']-m['cost']-m['fees'];m['contribution_margin_pct']=(m['contribution']/m['net']*100).quantize(Decimal('.01')) if m['net']>0 else None
 totals={k:sum((m[k] for m in channels.values()),Decimal(0)) for k in ('gross','refunds','cost','fees','net','contribution')}
 average=(totals['gross']/len(orders)).quantize(Decimal('.01'))
 alerts=[{'channel':c,'reason':'negative contribution after costs and fees'} for c,m in channels.items() if m['contribution']<0]
 def serialize(v):
  if isinstance(v,Decimal):return f'{v:.2f}'
  if isinstance(v,dict):return {k:serialize(x) for k,x in v.items()}
  if isinstance(v,list):return [serialize(x) for x in v]
  return v
 return serialize({'status':'ok','currency':next(iter(currencies)),'order_count':len(orders),'average_order_value':average,'totals':totals,'channels':channels,'daily_net':dict(sorted(daily.items())),'alerts':alerts})

def html(r):
 if r['status']!='ok':raise ValueError('cannot render invalid data')
 base={'status':'ok','currency':r['currency'],'gross':r['totals']['gross'],'refunds':r['totals']['refunds'],'net':r['totals']['net'],'transactions':r['order_count'],'average_positive_sale':r['average_order_value'],'daily':r['daily_net']}
 out=render(base).replace('Average positive sale','Average order value').replace('Transactions','Orders')
 rows=''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in [c,m['orders'],m['net'],m['cost'],m['fees'],m['contribution'],m['contribution_margin_pct']])+'</tr>' for c,m in r['channels'].items())
 section='<h2>Channel contribution</h2><p>Contribution = net sales − recorded product costs − recorded fees. This is not net profit.</p><div style="overflow:auto"><table style="width:100%;text-align:left"><tr><th>Channel</th><th>Orders</th><th>Net sales</th><th>Costs</th><th>Fees</th><th>Contribution</th><th>Margin %</th></tr>'+rows+'</table></div><h2>Exceptions requiring review</h2>' + ('<ul>'+''.join('<li>'+escape(a['channel']+': '+a['reason'])+'</li>' for a in r['alerts'])+'</ul>' if r['alerts'] else '<p>No negative-contribution channels in this sample.</p>')
 return out.replace('<footer>',section+'<footer>')

def main():
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--output',required=True);a=p.parse_args();r=analyze(a.source)
 if r['status']=='ok':
  target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
  import tempfile,os
  fd,tmp=tempfile.mkstemp(dir=target.parent)
  try:
   with os.fdopen(fd,'w') as f:f.write(html(r))
   os.replace(tmp,target)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
 print(json.dumps(r,indent=2));raise SystemExit(0 if r['status']=='ok' else 2)
if __name__=='__main__':main()
