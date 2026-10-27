"""Validated single-currency transaction reporting with a standalone HTML chart."""
import argparse
import csv
from datetime import date,timedelta
from decimal import Decimal,InvalidOperation
from collections import defaultdict
from pathlib import Path
from html import escape
import json
import os
import tempfile

def analyze(source):
    days=defaultdict(lambda:Decimal(0));rows=[];errors=[];currencies=set();ids=set()
    with open(source,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not {'transaction_id','date','amount','currency'}<=set(reader.fieldnames or []):raise ValueError('Required: transaction_id,date,amount,currency')
        for line,row in enumerate(reader,2):
            try:
                key=(row.get('transaction_id') or '').strip()
                if not key:raise ValueError('missing transaction_id')
                if key in ids:raise ValueError('duplicate transaction_id')
                day=date.fromisoformat(row['date'])
                amount=Decimal(row['amount'])
                if not amount.is_finite() or amount!=amount.quantize(Decimal('.01')):raise ValueError('amount must be finite with at most 2 decimal places')
                currency=row['currency'].strip().upper()
                if len(currency)!=3 or not currency.isascii() or not currency.isalpha():raise ValueError('currency must be a three-letter code')
                ids.add(key);currencies.add(currency);rows.append((day,amount));days[day]+=amount
            except (ValueError,InvalidOperation,TypeError) as exc:errors.append({'line':line,'reason':str(exc)})
    if len(currencies)>1:errors.append({'line':0,'reason':'mixed currencies; convert outside this report'})
    if not rows:errors.append({'line':0,'reason':'no valid transactions'})
    if errors:return {'status':'invalid','errors':errors}
    positive=[amount for _,amount in rows if amount>0];refunds=-sum((a for _,a in rows if a<0),Decimal(0))
    gross=sum(positive,Decimal(0));net=gross-refunds
    first,last=min(days),max(days)
    if (last-first).days>3660:return {'status':'invalid','errors':[{'line':0,'reason':'date range exceeds 3660 days'}]}
    for i in range((last-first).days+1):days[first+timedelta(days=i)]+=0
    return {'status':'ok','currency':next(iter(currencies)),'transactions':len(rows),'sales_transactions':len(positive),'refund_transactions':sum(a<0 for _,a in rows),'gross':str(gross),'refunds':str(refunds),'net':str(net),'average_positive_sale':str((gross/len(positive)).quantize(Decimal('.01'))) if positive else '0.00','refund_value_rate':str((refunds/gross*100).quantize(Decimal('.01'))) if gross else None,'daily':{d.isoformat():str(a) for d,a in sorted(days.items())}}

def render(result):
    if result['status']!='ok':raise ValueError('Invalid dataset cannot produce a sales report')
    daily=result['daily'];maxval=max([abs(Decimal(a)) for a in daily.values()]+[Decimal(1)])
    bars=''.join('<div class="row"><span>'+escape(day)+'</span><div class="track"><div style="width:'+str(abs(Decimal(value))/maxval*100)+'%;background:'+('#c24145' if Decimal(value)<0 else '#167e86')+'"></div></div><strong>'+escape(value)+'</strong></div>' for day,value in daily.items())
    cards=''.join('<article><span>'+label+'</span><h2>'+escape(str(result[key]))+'</h2></article>' for label,key in [('Gross sales','gross'),('Refund value','refunds'),('Net sales','net'),('Transactions','transactions'),('Average positive sale','average_positive_sale')])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sales report</title><style>body{font:16px system-ui;background:#edf3f7;color:#172c40;max-width:1050px;margin:50px auto;padding:24px}.cards{display:flex;gap:12px;flex-wrap:wrap}article{background:white;padding:18px;min-width:135px;border-radius:12px}h2{margin:12px 0}.row{display:flex;align-items:center;gap:15px;margin:18px 0}.track{flex:1;background:#dce6ed;height:25px}.track div{height:100%}strong{min-width:90px}span{font-size:14px}footer{margin-top:40px;color:#526477}</style><h1>Sales performance</h1><p>Currency: '+escape(result['currency'])+' · Single-currency transaction summary</p><div class="cards">'+cards+'</div><h2>Daily net sales</h2><p>Bar length represents magnitude; red indicates a negative daily total.</p>'+bars+'<footer>Personal portfolio demo. Fictional inputs. Refund value rate = refunds / gross sales; this is not a cohort return rate. No currency conversion or tax calculation.</footer></html>'

def write_report(source,destination):
    result=analyze(source)
    if result['status']=='ok':
        target=Path(destination);target.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(dir=target.parent,suffix='.tmp')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(render(result))
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--output',required=True);a=p.parse_args()
    result=write_report(a.source,a.output);print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='ok' else 2)
if __name__=='__main__':main()
