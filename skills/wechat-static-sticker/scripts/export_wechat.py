#!/usr/bin/env python3
"""Deterministic static WeChat asset exporter. No network or image generation."""
import argparse,io,json,re,zipfile
from pathlib import Path
from PIL import Image,ImageOps
SPECS={
 'main':(240,240,500000),'cover':(240,240,500000),'icon':(50,50,100000),
 'banner':(750,400,500000),'character_avatar':(240,240,500000),
 'character_icon':(50,50,100000),'artist_avatar':(640,640,500000),
 'artist_banner':(750,400,80000),'tip_guide':(750,560,100000),
 'tip_thanks':(750,750,200000)}
TRANSPARENT={'main','cover','icon','character_avatar','character_icon'}
JPEG={'banner','artist_banner','artist_avatar'}

def validate(m):
 mode=m.get('mode','album')
 if mode not in ('album','assets'):raise ValueError('mode must be album or assets')
 items=m.get('assets',[])
 if not items:raise ValueError('No assets supplied')
 mains=[a for a in items if a['role']=='main']
 if mode=='album':
  if not 8<=len(mains)<=24:raise ValueError('Album must have 8–24 main images')
  for r in ('cover','icon','banner'):
   if sum(a['role']==r for a in items)!=1:raise ValueError(f'Album requires exactly one {r}')
 seen=set()
 for a in items:
  if a['role'] not in SPECS:raise ValueError('Unknown role: '+a['role'])
  if a['role']=='main':
   word=a.get('meaning','')
   if not re.fullmatch(r'[\u4e00-\u9fff]{1,4}',word) or word in seen:raise ValueError('Meanings must be unique 1–4 Chinese characters')
   seen.add(word)
 for key,limit in [('album_name',8),('album_intro',80),('artist_name',10),('artist_intro',80),('copyright',10),('character_intro',80)]:
  value=m.get(key,'')
  if not isinstance(value,str) or len(value)>limit:raise ValueError(f'{key} exceeds {limit} characters')
  if value and re.search(r'[^\u4e00-\u9fffA-Za-z0-9\s，。！？、；：,.!?;:（）()\-]',value):raise ValueError(f'{key}: unsupported special character')
 if m.get('album_name') and not re.fullmatch(r'[\u4e00-\u9fffA-Za-z0-9]+',m['album_name']):raise ValueError('Album name cannot contain whitespace/punctuation')
 for r in SPECS:
  if r!='main' and sum(a['role']==r for a in items)>1:raise ValueError('Duplicate supporting role: '+r)

def encode(im,fmt,limit):
 b=io.BytesIO();im.save(b,format=fmt,optimize=True,**({'quality':95} if fmt=='JPEG' else {}))
 if len(b.getvalue())<=limit:return b.getvalue(),'original-colors'
 if fmt=='JPEG':
  for q in [92,88,84,80,76,72,68,64,60]:
   b=io.BytesIO();im.save(b,format='JPEG',quality=q,optimize=True)
   if len(b.getvalue())<=limit:return b.getvalue(),f'JPEG quality {q}'
 else:
  for colors in [256,192,128,96,64]:
   q=im.quantize(colors=colors,method=Image.Quantize.FASTOCTREE if im.mode=='RGBA' else Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
   b=io.BytesIO();q.save(b,format='PNG',optimize=True)
   if len(b.getvalue())<=limit:return b.getvalue(),f'{colors} colors; visual review required'
 raise ValueError(f'Cannot meet {limit} bytes without excessive quality loss; simplify artwork or confirm current backend limit')

def run(manifest,output):
 m=json.loads(manifest.read_text());validate(m)
 if output.exists():raise ValueError('Output must be a new directory; existing files are never overwritten')
 prepared=[]
 for i,a in enumerate(m['assets'],1):
  role=a['role'];w,h,limit=SPECS[role]
  if 'max_bytes' in a:
   if not a.get('limit_source'):raise ValueError('Limit override needs limit_source')
   limit=int(a['max_bytes'])
   if limit<=0:raise ValueError('Invalid byte limit')
  source=Path(a['path']);source=source if source.is_absolute() else manifest.parent/source
  with Image.open(source) as raw:
   if getattr(raw,'is_animated',False):raise ValueError('Animated input unsupported by static exporter; never silently flatten GIF')
   im=ImageOps.exif_transpose(raw).convert('RGBA')
  transparent=role in TRANSPARENT
  if transparent:
   if im.getchannel('A').getextrema()[0]==255:raise ValueError(f'{role}: transparent artwork required; generate or extract first')
   # Preserve existing framing; do not unexpectedly crop captions or enlarge.
   im.thumbnail((w,h),Image.Resampling.LANCZOS)
   canvas=Image.new('RGBA',(w,h));canvas.alpha_composite(im,((w-im.width)//2,(h-im.height)//2));im=canvas
  else:
   if abs(im.width/im.height-w/h)/(w/h)>0.03:raise ValueError(f'{role}: aspect ratio mismatch, re-layout before export')
   if im.getchannel('A').getextrema()[0]<255:raise ValueError(f'{role}: opaque artwork required')
   im=ImageOps.fit(im.convert('RGB'),(w,h),method=Image.Resampling.LANCZOS)
  fmt='JPEG' if role in JPEG else 'PNG';data,method=encode(im,fmt,limit)
  fname=f'{role}/{i:02d}'+('.jpg' if fmt=='JPEG' else '.png')
  check=Image.open(io.BytesIO(data));assert check.size==(w,h) and len(data)<=limit
  prepared.append((fname,data,{'file':fname,'role':role,'size':[w,h],'format':fmt,'bytes':len(data),'limit':limit,'encoding':method,'meaning':a.get('meaning',''),'limit_source':a.get('limit_source','references/wechat-specs.md')}))
 output.mkdir(parents=True)
 for fname,data,_ in prepared:
  p=output/fname;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
 report={'status':'technical_checks_passed_not_platform_approved','mode':m.get('mode','album'),'files':[r for _,_,r in prepared],'visual_review':'required','rights_review':'not_automated','tip_specs':'user-supplied provisional targets'}
 (output/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 # No source paths or reference photos enter the upload bundle.
 metadata={k:v for k,v in m.items() if k not in ('assets',)}
 metadata['meanings']=[{'file':r['file'],'meaning':r['meaning']} for _,_,r in prepared if r['role']=='main']
 (output/'submission.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
 (output/'状态说明.txt').write_text('技术规格检查通过；未提交平台审核。请视觉复核文字、透明边缘、构图和风格；版权、重名与AI申报须据实核对。赞赏规格为用户提供的暂定制作目标，以后台提示为准。')
 with zipfile.ZipFile(output/'upload.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(output.rglob('*')):
   if p.is_file() and p.name!='upload.zip':z.write(p,str(p.relative_to(output)))
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 try:run(a.manifest.resolve(),a.output.resolve())
 except (ValueError,OSError,KeyError,TypeError) as e:p.exit(2,f'Export stopped: {e}\n')
