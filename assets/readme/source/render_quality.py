#!/usr/bin/env python3
"""Lossless, full-color 2× WebP from the original editable SVG scene layers.

Retains the v3 timing and 20 FPS, merges identical frames before encoding, and
never quantizes colors. The earlier GIFs remain independent compatibility assets.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageDraw
from render_motion import isolate, ease, progress

HERE=Path(__file__).resolve().parent
ASSETS=HERE.parent

def render(svg,node,spec):
    scale=1.5 if 'compact' in svg.stem else 2
    root=ET.parse(svg).getroot()
    ids=[layer['id'] for layer in spec['layers']]
    masks=sorted({layer['mask'] for layer in spec['layers'] if layer.get('mask')})
    base=copy.deepcopy(root)
    for parent in base.iter():
        for child in list(parent):
            if child.get('id') in ids:
                parent.remove(child)
    with tempfile.TemporaryDirectory(prefix='profile-full-color-') as temp:
        tmp=Path(temp);jobs=[]
        for label,tree in [('base',base),('settled',root)]+[(i,isolate(root,i)) for i in ids+masks]:
            file=tmp/f'{label}.svg'
            ET.ElementTree(tree).write(file,encoding='utf-8',xml_declaration=True)
            jobs.append({'input':str(file),'output':str(file.with_suffix('.png')),'scale':scale})
        (tmp/'jobs.json').write_text(json.dumps(jobs))
        subprocess.run([node,str(HERE/'rasterize.cjs'),str(tmp/'jobs.json')],check=True)
        base_image=Image.open(tmp/'base.png').convert('RGBA')
        layers={i:Image.open(tmp/f'{i}.png').convert('RGBA') for i in ids}
        masks={i:Image.open(tmp/f'{i}.png').getchannel('A') for i in masks}
        alpha=base_image.getchannel('A')
        frames=[];durations=[];last_hash=None
        hold_reference=None
        for frame in range(round(spec['duration']*spec['fps'])):
            t=frame/spec['fps'];canvas=base_image.copy()
            for layer in spec['layers']:
                p=progress(t,*layer.get('exit',spec['exit']))
                exit_alpha=1-p*p*(3-2*p)
                raw_entry=progress(t,layer['start'],layer['end']);entry=ease(raw_entry)
                opacity=entry*exit_alpha
                if opacity<=0:continue
                raster=layers[layer['id']].copy()
                if layer.get('reveal'):
                    bbox=raster.getbbox();reveal=raw_entry if layer.get('steps') else entry
                    if layer.get('steps'):reveal=int(reveal*layer['steps'])/layer['steps']
                    edge=round(bbox[0]+(bbox[2]-bbox[0])*reveal)
                    mask=Image.new('L',raster.size,0)
                    ImageDraw.Draw(mask).rectangle((0,0,edge,raster.height),fill=255)
                    raster.putalpha(ImageChops.multiply(raster.getchannel('A'),mask))
                    opacity=exit_alpha
                raster.putalpha(raster.getchannel('A').point(lambda a:round(a*opacity)))
                dx,dy=layer.get('from',[0,0]);mx,my=layer.get('drift',[0,0])
                travel=.94 if 'compact' in svg.stem else 1
                drift=progress(t,*layer.get('drift_time',[0,1]))
                positioned=Image.new('RGBA',canvas.size)
                positioned.alpha_composite(raster,(round((dx*(1-entry)+mx*drift)*travel*scale),round((dy*(1-entry)+my*drift)*travel*scale)))
                if layer.get('mask'):
                    positioned.putalpha(ImageChops.multiply(positioned.getchannel('A'),masks[layer['mask']]))
                canvas.alpha_composite(positioned)
            canvas.putalpha(alpha)
            # Ignore RGB under zero alpha when checking exact visible fidelity.
            visible=Image.new('RGBA',canvas.size)
            visible.paste(canvas,mask=alpha.point(lambda a:255 if a else 0))
            digest=hashlib.sha256(visible.tobytes()).hexdigest()
            if digest==last_hash:durations[-1]+=round(1000/spec['fps'])
            else:
                frames.append(visible);durations.append(round(1000/spec['fps']));last_hash=digest
            if abs(t-5.2)<.001:hold_reference=visible.copy()
        output=svg.with_suffix('.webp')
        hold_reference.save(ASSETS/'preview'/f'{svg.stem}-source-hold.png')
        print(f'Encoding {output.name}: {base_image.size}, {len(frames)} unique frames',flush=True)
        frames[0].save(output,format='WEBP',save_all=True,append_images=frames[1:],duration=durations,
                       loop=0,lossless=True,quality=80,method=4,minimize_size=True,exact=True)
        expected_first=frames[0].tobytes()
        del frames,layers,masks
        hashes=[];timeline=[];elapsed=0;hold_hash=None;max_colors=0
        with Image.open(output) as animation:
            assert animation.info.get('loop')==0
            for i in range(animation.n_frames):
                animation.seek(i);decoded=animation.convert('RGBA');decoded.load()
                rgba=Image.new('RGBA',decoded.size)
                rgba.paste(decoded,mask=decoded.getchannel('A').point(lambda a:255 if a else 0))
                timestamp=animation.info['timestamp'];duration=animation.info['duration']
                digest=hashlib.sha256(rgba.tobytes()).hexdigest()
                hashes.append(digest);timeline.append((timestamp,digest))
                assert rgba.getpixel((0,0))[3]==0
                elapsed=timestamp+duration
                if timestamp<=5200<elapsed:
                    assert rgba.tobytes()==hold_reference.tobytes(),'Lossless hold differs from rendered source'
                    hold_hash=digest
                    rgba.save(ASSETS/'preview'/f'{svg.stem}-full-color.png')
                    max_colors=len(rgba.convert('RGB').getcolors(maxcolors=16777216) or [])
        assert elapsed==round(spec['duration']*1000)
        assert hashes[0]==hashes[-1]==hashlib.sha256(expected_first).hexdigest()
        assert all(h==hold_hash for t,h in timeline if spec['hold'][0]*1000<=t<spec['hold'][1]*1000)
        assert max_colors>256
        assert output.stat().st_size<8_000_000,'Full-color animation exceeds 8 MB budget'
        return {'asset':output.name,'dimensions':list(base_image.size),'bytes':output.stat().st_size,
                'encoded_frames':len(hashes),'duration_ms':elapsed,'source_fps':spec['fps'],
                'hold_colors':max_colors,'encoding':'lossless RGBA WebP','hold_matches_source_exactly':True,
                'hold_pixel_still':True,'loop_boundary_identical':True,'rounded_corners_transparent':True}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--node',default='node');parser.add_argument('--asset')
    args=parser.parse_args();spec=json.loads((HERE/'motion.json').read_text())
    (ASSETS/'preview').mkdir(exist_ok=True)
    sources=[ASSETS/args.asset] if args.asset else sorted(ASSETS.glob('hero-*.svg'))
    results=[render(svg,args.node,spec) for svg in sources]
    receipt=ASSETS/'preview'/'quality-checks.json'
    previous=json.loads(receipt.read_text()) if args.asset and receipt.exists() else []
    changed={r['asset'] for r in results}
    receipt.write_text(json.dumps([r for r in previous if r['asset'] not in changed]+results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
