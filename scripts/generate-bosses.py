"""Confirmed plan queue. Respects account concurrency; resume without duplicating clips."""
import os,json,time,urllib.request,re,pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'generation-records';OUT.mkdir(exist_ok=True)
CHARS=[('Rei Esqueleto','6124e110-2675-4e65-9564-3978479b6880','prepare sword, slash powerfully forward at middle of sequence, recover'),('Arquilich','8c9ae77f-2206-496e-adf6-0f6dbc503986','raise skull staff, thrust forward casting magic at middle of sequence, recover'),('Senhor Minotauro','a6266665-b6d3-4a04-adb5-c4ab0a7b21cb','lift heavy axe then smash forward at middle of sequence, recover'),('Titã de Gelo','785aa7bd-06fa-48d7-bc15-c815d3b414b4','raise both icy arms then slam forward at middle of sequence, recover')]
DIRS=['south','south-west','west','north-west','north','north-east','east','south-east']
CLIPS=[('idle','breathing-idle'),('walk','walking-6-frames'),('run','running-6-frames'),('attack',None),('hurt','taking-punch'),('death','falling-back-death')]
def call(name,args):
 p={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}
 req=urllib.request.Request(os.environ['PIXELLAB_API_URL']+'/mcp',data=json.dumps(p).encode(),headers={'Authorization':'Bearer '+os.environ['PIXELLAB_API_TOKEN'],'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
 with urllib.request.urlopen(req,timeout=180) as r:s=r.read().decode()
 d=json.loads(next(l[6:] for l in s.splitlines() if l.startswith('data: ')))
 if 'error' in d:raise RuntimeError(str(d['error']))
 return '\n'.join(c.get('text','') for c in d['result'].get('content',[]) if c.get('type')=='text')
def main():
 tasks=[]
 for name,cid,action in CHARS:
  text=call('get_character',{'character_id':cid,'include_preview':False});(OUT/(cid+'-initial.txt')).write_text(text)
  for clip,template in CLIPS:
   record=OUT/(cid+'-'+clip+'.json')
   if record.exists():info=json.loads(record.read_text())
   else:
    pattern=rf'^  {clip} .*?\[group: ([^\]]+)\]'
    found=re.search(pattern,text,re.M)
    info={'group':found.group(1) if found else None,'submitted':list(DIRS) if found else [],'jobs':[]}
   for direction in DIRS:
    if direction not in info['submitted']:tasks.append((name,cid,action,clip,template,direction,record,info))
 print('Pending direction tasks',len(tasks),flush=True)
 while tasks:
  t=tasks[0];name,cid,action,clip,template,direction,record,info=t
  args={'character_id':cid,'animation_name':clip,'directions':[direction]}
  if info['group']:args['animation_group_id']=info['group']
  if template:args.update(mode='template',template_animation_id=template)
  else:args.update(mode='v3',frame_count=8,keep_first_frame=False,action_description=f'{action}. Clearly prepare, strike midway, and recover to starting stance. Preserve identity and weapon.')
  try:result=call('animate_character',args)
  except Exception as e:print('Transport',e,flush=True);time.sleep(20);continue
  if 'error:' in result.lower():
   if 'slot' in result or '429' in result:
    print('Waiting for free slots',flush=True);call('wait_for_jobs',{'timeout_seconds':120,'min_finished':1});continue
   print('STOP',result,flush=True);(OUT/'queue-error.txt').write_text(result);return
  match=re.search(r'^group: (\S+)',result,re.M)
  if not match:print('Unrecognized receipt',result,flush=True);return
  info['group']=match.group(1);info['submitted'].append(direction);info['jobs'].append(result);record.write_text(json.dumps(info,indent=2))
  tasks.pop(0);print(name,clip,direction,'remaining',len(tasks),flush=True)
 while True:
  text=call('list_jobs',{});
  if 'no active' in text.lower() or 'no running' in text.lower() or '0 active' in text.lower():break
  print('Finishing',text[:120],flush=True)
  result=call('wait_for_jobs',{'timeout_seconds':240,'min_finished':10})
  if 'none' in result.lower() and 'running' in result.lower():break
  if 'no ' in result.lower() and 'jobs' in result.lower():break
 for name,cid,_ in CHARS:(OUT/(cid+'-final.txt')).write_text(call('get_character',{'character_id':cid,'include_preview':False}))
 print('DONE',flush=True)
if __name__=='__main__':main()
