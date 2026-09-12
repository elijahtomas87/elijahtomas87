#!/usr/bin/env python3
"""Check every embed, SVG safety, contrast, and the complete encoded GIF hold."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image

ASSETS = Path(__file__).resolve().parents[1]
ROOT = ASSETS.parents[1]

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs=[]
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if tag=='img':
            assert data.get('alt','').strip(), 'Empty image description'
        if tag in ['source','img','a']:
            ref=data.get('srcset') or data.get('src') or data.get('href')
            if ref:
                self.refs.append(ref)

def luminance(color):
    values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))

def main():
    checked=[]
    for md in [ROOT/'README.md',ASSETS/'static.md']:
        parser=Images();parser.feed(md.read_text())
        assert '<script' not in md.read_text()
        for ref in parser.refs:
            if not ref.startswith(('https://','#')):
                assert (md.parent/ref).resolve().is_file(), ref
        checked.append({'markdown':md.name,'local_embeds_and_links':sum(not r.startswith(('https://','#')) for r in parser.refs)})
    svgs=list(ASSETS.glob('*.svg'))
    for svg in svgs:
        root=ET.parse(svg).getroot()
        assert root.get('viewBox')
        tags=[node.tag.split('}')[-1] for node in root.iter()]
        assert 'title' in tags and 'desc' in tags
        assert not set(tags)&{'script','foreignObject','animate','animateTransform','image'}
        if 'style' in tags:
            assert svg.name.startswith('contributions-') and '-still' not in svg.name
            styles=''.join(n.text or '' for n in root.iter() if n.tag.endswith('}style'))
            assert not re.search(r'url\s*\(|@import|https?:|javascript:',styles,re.I)
            assert 'prefers-reduced-motion:reduce' in styles
        ids=[node.get('id') for node in root.iter() if node.get('id')]
        assert len(ids)==len(set(ids))
        for node in root.iter():
            assert not any(key.startswith('on') or key.endswith('href') for key in node.attrib)
    gifs=[]
    spec=json.loads((ASSETS/'source/motion.json').read_text())
    hold_start,hold_end=[round(t*1000) for t in spec['hold']]
    for file in sorted(ASSETS.glob('hero-*.gif')):
        timeline=[];elapsed=0
        with Image.open(file) as gif:
            for i in range(gif.n_frames):
                gif.seek(i);rgba=gif.convert('RGBA')
                timeline.append((elapsed,rgba.tobytes()))
                assert rgba.getpixel((0,0))[3]==0
                assert rgba.getpixel((40,40))[3]==255
                elapsed+=gif.info['duration']
        hold=[pixels for time,pixels in timeline if hold_start<=time<hold_end]
        reference=max((row for row in timeline if row[0]<=hold_start),key=lambda row:row[0])[1]
        assert all(pixels==reference for pixels in hold)
        assert timeline[0][1]==timeline[-1][1]
        assert elapsed==round(spec['duration']*1000)
        assert file.stat().st_size<spec['max_size_bytes']
        gifs.append({'asset':file.name,'bytes':file.stat().st_size,'duration_ms':elapsed,'full_hold_unchanged':True,'loop_boundary_identical':True})
    palettes=json.loads((ASSETS/'source/palette.json').read_text())
    contrast={}
    for theme,c in palettes.items():
        bg=luminance(c['bg'])
        contrast[theme]={}
        for role in ['fg','muted','primary','amber','teal']:
            value=luminance(c[role]);ratio=(max(bg,value)+.05)/(min(bg,value)+.05)
            assert ratio>=4.5,(theme,role,ratio)
            contrast[theme][role]=round(ratio,2)
        plate=luminance(c['edge'])
        for role in ['primary','amber','teal']:
            value=luminance(c[role]);ratio=(max(plate,value)+.05)/(min(plate,value)+.05)
            assert ratio>=3,(theme,role,'tool plate',ratio)
            contrast[theme][role+'_on_tool_plate']=round(ratio,2)
    result={'scope':'Local assets only','readmes':checked,'svg_count':len(svgs),'svg_checks':'passed','contrast':contrast,'animations':gifs}
    (ASSETS/'preview/asset-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
