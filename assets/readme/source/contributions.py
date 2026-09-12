#!/usr/bin/env python3
"""Build a truthful purple contribution calendar, with a decorative scanner.

The scanner never changes a cell's count or intensity. Both responsive layouts
contain every source date exactly once. No synthetic activity or secret token.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
ASSETS=HERE.parent
USERNAME='elijahtomas87'
SOURCE=f'https://github.com/users/{USERNAME}/contributions'

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__();self.cells={};self.labels={};self.current=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='td' and 'data-date' in a and 'data-level' in a:
            self.cells[a['id']]={'date':a['data-date'],'level':int(a['data-level'])}
        if tag=='tool-tip' and a.get('for','').startswith('contribution-day-component-'):
            self.current=a['for'];self.labels[self.current]=''
    def handle_data(self,data):
        if self.current:self.labels[self.current]+=data
    def handle_endtag(self,tag):
        if tag=='tool-tip':self.current=None

def parse_public(html):
    parser=CalendarParser();parser.feed(html);days=[]
    for key,cell in parser.cells.items():
        label=parser.labels.get(key,'').strip()
        match=re.match(r'(No|[\d,]+) contributions? on ',label)
        if not match:raise ValueError(f'Missing contribution count for {cell["date"]}')
        count=0 if match[1]=='No' else int(match[1].replace(',',''))
        days.append({**cell,'count':count})
    days.sort(key=lambda d:d['date'])
    if not 360<=len(days)<=371:raise ValueError('Unexpected calendar length; refusing partial data')
    return {'username':USERNAME,'source':SOURCE,'retrieved_at':datetime.now(timezone.utc).isoformat(),
            'visibility':'public profile calendar; follows GitHub private-contribution visibility',
            'start':days[0]['date'],'end':days[-1]['date'],'reported_total':sum(d['count'] for d in days),
            'counts':[d['count'] for d in days],'levels':''.join(str(d['level']) for d in days)}

def validate(data):
    start=date.fromisoformat(data['start']);end=date.fromisoformat(data['end'])
    counts=data['counts'];levels=data['levels']
    assert len(counts)==len(levels)==(end-start).days+1
    assert 360<=len(counts)<=371
    assert all(isinstance(c,int) and c>=0 for c in counts)
    assert all(l in '01234' for l in levels)
    assert all((c>0)==(int(l)>0) for c,l in zip(counts,levels))
    assert sum(counts)==data['reported_total']
    assert data['username']==USERNAME
    return [{'date':(start+timedelta(days=i)).isoformat(),'count':c,'level':int(levels[i])} for i,c in enumerate(counts)]

def render(data,theme,compact=False,animated=True):
    days=validate(data);dark=theme=='dark'
    bg='#0D1117' if dark else '#FFFFFF';fg='#E6EDF3' if dark else '#1F2328'
    muted='#9198A1' if dark else '#656D76';line='#3D444D' if dark else '#D1D9E0'
    colors=['#161B22','#68428A','#9462BC','#BE87E4','#E1B3FF'] if dark else ['#EFF2F5','#CFB7E2','#AB7ECC','#8852B0','#622C90']
    accent=fg
    width,height=(720,640) if compact else (1200,386)
    first=date.fromisoformat(days[0]['date']);offset=(first.weekday()+1)%7
    weeks=(len(days)+offset+6)//7
    ranges=[(0,27,224),(27,weeks,415)] if compact else [(0,weeks,168)]
    cell,gap=(18,5) if compact else (14,6)
    step=cell+gap;x0=54 if compact else 76
    total=sum(d['count'] for d in days);active=sum(d['count']>0 for d in days)
    fetched=datetime.fromisoformat(data['retrieved_at'].replace('Z','+00:00')).date()
    scope='Includes private activity' if 'authenticated' in data['visibility'] else 'Publicly visible GitHub activity'
    end=date.fromisoformat(data['end'])
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
         '<title id="title">GitHub contributions</title>',
         f'<desc id="desc">{total:,} authentic GitHub contributions across {active} active days, from {data["start"]} through {data["end"]}. {scope}. Retrieved {escape(data["retrieved_at"])}. Each square is one day. A decorative scanning marker moves across an unchanged calendar; it does not create activity.</desc>',
         f'<metadata>{escape(json.dumps({"source":data["source"],"retrieved_at":data["retrieved_at"],"total":total,"days":len(days),"visibility":data["visibility"]},separators=(",",":")))}</metadata>']
    # One blurred underlay per calendar band keeps the effect inexpensive.
    # Crisp cells are painted afterward, preserving all fills and empty days.
    out.append('<defs><filter id="activity-glow" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="2.2"/></filter></defs>')
    if animated:
        travel=(27 if compact else weeks)*step-3
        out.append(f'<style>@keyframes sweep{{0%,8%{{transform:translateX(0);opacity:0}}12%{{opacity:.75}}78%{{transform:translateX({travel}px);opacity:.75}}82%,100%{{transform:translateX({travel}px);opacity:0}}}}.scanner{{animation:sweep 14s linear infinite}}.second{{animation-delay:7s}}@media(prefers-reduced-motion:reduce){{.scanner{{display:none;animation:none}}}}</style>')
    out.append(f'<rect x=".75" y=".75" width="{width-1.5}" height="{height-1.5}" rx="22" fill="{bg}" stroke="{line}" stroke-width="1.5"/>')
    out.append(f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" fill="{fg}">')
    def text(x,y,size,value,color=fg,extra=''):
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(value)}</text>'
    out.append(text(36,43,18 if compact else 13,'ACTIVITY RECORD',muted,'letter-spacing="2.5"'))
    out.append(text(36,88,40 if compact else 36,'GitHub contributions'))
    if compact:
        out.extend([text(36,144,34,f'{total:,}',accent,'font-weight="650"'),text(151,143,20,'contributions',muted),
                    text(390,143,24,str(active),accent,'font-weight="650"'),text(448,143,20,'active days',muted)])
    else:
        out.extend([text(1164,60,37,f'{total:,}',accent,'text-anchor="end" font-weight="650"'),
                    text(1164,87,16,f'contributions · {active} active days',muted,'text-anchor="end"')])
    out.append(text(36,181 if compact else 120,20 if compact else 15,f'{first:%b %Y} — {end:%b %Y}',muted))
    drawn=[]
    for segment,(begin,finish,y0) in enumerate(ranges):
        out.append(f'<g aria-hidden="true" pointer-events="none" filter="url(#activity-glow)" opacity="{.75 if dark else .45}">')
        for index,d in enumerate(days):
            wi,weekday=divmod(index+offset,7)
            if begin<=wi<finish and d['count']>0:
                x=x0+(wi-begin)*step;y=y0+weekday*step
                out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{colors[d["level"]]}"/>')
        out.append('</g>')
        months=set()
        for index,d in enumerate(days):
            wi,weekday=divmod(index+offset,7)
            if not begin<=wi<finish:continue
            day=date.fromisoformat(d['date']);x=x0+(wi-begin)*step;y=y0+weekday*step
            month=(day.year,day.month)
            if weekday==0 and month not in months and x<x0+(finish-begin)*step-34:
                out.append(text(x,y0-16,20 if compact else 13,day.strftime('%b'),muted));months.add(month)
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{colors[d["level"]]}" data-date="{d["date"]}" data-count="{d["count"]}" data-level="{d["level"]}"><title>{d["date"]}: {d["count"]} contributions</title></rect>')
            drawn.append(d['date'])
        for row,label in [(1,'M'),(3,'W'),(5,'F')]:out.append(text(x0-25,y0+row*step+cell-2,20 if compact else 12,label,muted))
        if animated:
            out.append(f'<g transform="translate({x0-3} {y0-8})"><g class="scanner {"second" if segment else ""}" opacity="0"><path d="M0 0V{7*step+2}" stroke="{accent}" stroke-opacity=".55" stroke-width="1.4"/><circle cy="-5" r="3.5" fill="{accent}"/></g></g>')
    assert sorted(drawn)==[d['date'] for d in days]
    legend_y=598 if compact else 344
    small=20 if compact else 12
    out.append(text(36,legend_y,small,scope,muted))
    out.append(text(36,legend_y+24,small,f'Snapshot · {fetched:%d %b %Y}',muted))
    legend_x=width-215
    out.append(text(legend_x-(58 if compact else 39),legend_y,small,'Less',muted))
    for i,color in enumerate(colors):out.append(f'<rect x="{legend_x+i*24}" y="{legend_y-12}" width="16" height="16" rx="3" fill="{color}"/>')
    out.append(text(legend_x+125,legend_y,small,'More',muted))
    out.append('</g></svg>')
    return '\n'.join(out)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path)
    parser.add_argument('--public-html',type=Path);parser.add_argument('--fetch-public',action='store_true')
    parser.add_argument('--output-dir',type=Path,default=ASSETS)
    args=parser.parse_args()
    if args.input:data=json.loads(args.input.read_text())
    elif args.public_html:data=parse_public(args.public_html.read_text())
    elif args.fetch_public:
        request=Request(SOURCE,headers={'User-Agent':'profile-contribution-preview','Accept':'text/html'})
        with urlopen(request,timeout=30) as response:
            if response.status!=200:raise RuntimeError('GitHub calendar request failed')
            data=parse_public(response.read().decode('utf-8'))
    else:parser.error('An authentic source is required: --input, --public-html or --fetch-public')
    days=validate(data);args.output_dir.mkdir(parents=True,exist_ok=True)
    for theme in ['light','dark']:
        for compact in [False,True]:
            for animated in [False,True]:
                stem=f'contributions-{theme}'+('-compact' if compact else '')+('' if animated else '-still')
                (args.output_dir/f'{stem}.svg').write_text(render(data,theme,compact,animated))
    receipt={k:data[k] for k in ['source','retrieved_at','start','end','visibility']}
    receipt.update({'total':sum(d['count'] for d in days),'active_days':sum(d['count']>0 for d in days),'dates':len(days),'date_weighted_count':sum((i+1)*d['count'] for i,d in enumerate(days)),'all_source_dates_preserved':True,'animation_changes_counts':False})
    (args.output_dir/'contribution-source.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
