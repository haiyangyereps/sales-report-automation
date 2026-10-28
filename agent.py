import argparse,json
from pathlib import Path
from agent_runtime import Provider,FixtureProvider,Journal,tool,run_agent,load_config
TEXT={'type':'string'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--config');p.add_argument('--prompt',default=DEFAULT_PROMPT);p.add_argument('--journal',default='agent-journal.db');p.add_argument('--source',default=DEFAULT_SOURCE);p.add_argument('--fixture',action='store_true');p.add_argument('--output',default='agent-result.json');p.add_argument('--review');p.add_argument('--reviewer');p.add_argument('--decision',choices=['approved','rejected']);a=p.parse_args()
 if a.config:load_config(a.config)
 j=Journal(a.journal)
 if a.review:
  if not a.reviewer or not a.decision:p.error('reviewer and decision required')
  print(json.dumps(j.review(a.review,a.reviewer,a.decision)));return
 tools,handlers,steps=configure(a.source,j)
 provider=FixtureProvider(steps) if a.fixture else Provider()
 result=run_agent(provider,j,a.prompt,tools,handlers,POLICY,mode='scripted_fixture' if a.fixture else 'live_model')
 Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False));print(json.dumps({'run_id':result['id'],'mode':result['mode'],'status':result['status'],'output':a.output}))

import business
DEFAULT_SOURCE='examples/orders.csv'
DEFAULT_PROMPT='Use tools to review channel contribution and inspect the main exception. Create a pending management review task using propose_review_task. Then summarize the tool results, distinguish facts from hypotheses, and state the actual proposal ID.'
POLICY='You are a sales reporting analyst. All numeric facts must come from metric tools. Contribution is not net profit. Do not infer causal explanations or missing costs. Label recommendations as hypotheses. Do not change source transactions. When asked to propose a review task, call propose_review_task; prose alone does not create a task. Do not claim an approval or a queued task without the corresponding tool result.'
def configure(source,j):
 result=business.analyze(source)
 if result['status']!='ok':raise ValueError('Source data validation failed; no model analysis allowed')
 def metrics(a,r):return result
 def channel(a,r):
  if a['channel'] not in result['channels']:raise ValueError('Unknown channel')
  return {'channel':a['channel'],'currency':result['currency'],'metrics':result['channels'][a['channel']]}
 def propose(a,r):
  evidence=channel(a,r)
  return j.propose(r,{'kind':'analysis_review','channel':a['channel'],'recommendation':a['recommendation'],'evidence':evidence})
 tools=[tool('get_sales_metrics','Read validated metrics calculated with Decimal, including alerts',{}),tool('get_channel_metrics','Inspect a single sales channel',{'channel':TEXT}),tool('propose_review_task','Queue an evidence-linked management review task',{'channel':TEXT,'recommendation':TEXT})]
 return tools,{'get_sales_metrics':metrics,'get_channel_metrics':channel,'propose_review_task':propose},[('get_sales_metrics',{}),('get_channel_metrics',{'channel':'marketplace'}),('propose_review_task',{'channel':'marketplace','recommendation':'Review recorded fees, costs and refunds before deciding whether to expand this channel.'}),'SCRIPTED FIXTURE: Marketplace contribution is -47.00 USD in the sample. This is not net profit. A review task is pending.']

if __name__=='__main__':main()
