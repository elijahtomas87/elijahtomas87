#!/usr/bin/env python3
"""Render SVG layers with Sharp; encode with Pillow, without ffmpeg.

Layer separation, short eased entry, still hold and reset follow the
beautify-github-readme motion workflow. All geometry comes from editable SVGs.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
ET.register_namespace('', 'http://www.w3.org/2000/svg')

def ease(t):
    return 1 - (1 - max(0, min(1, t))) ** 3

def progress(t, start, end):
    return max(0, min(1, (t-start)/(end-start)))

def find_chain(root, target):
    if root.get('id') == target:
        return [root]
    for child in root:
        chain = find_chain(child, target)
        if chain:
            return [root] + chain
    return None

def isolate(root, target):
    chain = find_chain(root, target)
    if not chain:
        raise ValueError(f'Missing SVG layer: {target}')
    result = ET.Element(root.tag, root.attrib)
    for child in root:
        if child.tag.endswith('}defs'):
            result.append(copy.deepcopy(child))
    parent = result
    for ancestor in chain[1:-1]:
        shell = ET.SubElement(parent, ancestor.tag, ancestor.attrib)
        parent = shell
    layer=copy.deepcopy(chain[-1])
    if layer.get('data-motion-only')=='true':
        layer.set('opacity','1')
    parent.append(layer)
    return result

def render(svg, node, spec):
    root = ET.parse(svg).getroot()
    layer_ids = [layer['id'] for layer in spec['layers']]
    mask_ids = sorted({layer['mask'] for layer in spec['layers'] if layer.get('mask')})
    base = copy.deepcopy(root)
    for parent in base.iter():
        for child in list(parent):
            if child.get('id') in layer_ids:
                parent.remove(child)
    with tempfile.TemporaryDirectory(prefix='et-motion-') as temp:
        tmp = Path(temp)
        jobs = []
        for label, tree in [('base', base), ('settled', root)] + [(i, isolate(root,i)) for i in layer_ids+mask_ids]:
            path = tmp / f'{label}.svg'
            ET.ElementTree(tree).write(path, encoding='utf-8', xml_declaration=True)
            jobs.append({'input':str(path), 'output':str(path.with_suffix('.png'))})
        (tmp/'jobs.json').write_text(json.dumps(jobs))
        subprocess.run([node, str(HERE/'rasterize.cjs'), str(tmp/'jobs.json')], check=True)
        base_image = Image.open(tmp/'base.png').convert('RGBA')
        layers = {i:Image.open(tmp/f'{i}.png').convert('RGBA') for i in layer_ids}
        masks = {i:Image.open(tmp/f'{i}.png').convert('RGBA').getchannel('A') for i in mask_ids}
        alpha = base_image.getchannel('A')
        # A reserved transparent index preserves the same rounded silhouette.
        background = base_image.getpixel((40,40))[:3]
        frames = []
        for frame in range(round(spec['duration'] * spec['fps'])):
            t = frame / spec['fps']
            canvas = base_image.copy()
            for layer in spec['layers']:
                p = progress(t, *layer.get('exit',spec['exit']))
                exit_alpha = 1 - p*p*(3-2*p)
                raw_entry=progress(t, layer['start'], layer['end'])
                entry = ease(raw_entry)
                opacity = entry * exit_alpha
                if opacity <= 0:
                    continue
                raster = layers[layer['id']].copy()
                if layer.get('reveal'):
                    bbox=raster.getbbox()
                    reveal=raw_entry if layer.get('steps') else entry
                    if layer.get('steps'):
                        reveal=int(reveal*layer['steps'])/layer['steps']
                    edge=round(bbox[0]+(bbox[2]-bbox[0])*reveal)
                    mask=Image.new('L',raster.size,0)
                    ImageDraw.Draw(mask).rectangle((0,0,edge,raster.height),fill=255)
                    raster.putalpha(ImageChops.multiply(raster.getchannel('A'),mask))
                    opacity=exit_alpha
                raster.putalpha(raster.getchannel('A').point(lambda a: round(a*opacity)))
                dx,dy = layer.get('from',[0,0])
                # Offsets are in canvas pixels; compact composition uses less travel.
                travel = .94 if 'compact' in svg.stem else 1
                drift=progress(t,*layer.get('drift_time',[0,1]))
                mx,my=layer.get('drift',[0,0])
                positioned=Image.new('RGBA',canvas.size)
                positioned.alpha_composite(raster, (round((dx*(1-entry)+mx*drift)*travel),round((dy*(1-entry)+my*drift)*travel)))
                if layer.get('mask'):
                    positioned.putalpha(ImageChops.multiply(positioned.getchannel('A'),masks[layer['mask']]))
                canvas.alpha_composite(positioned)
            canvas.putalpha(alpha)
            # Opaque canvas matte keeps antialiasing clean at the rounded edge.
            rgb = Image.new('RGB', canvas.size, background)
            rgb.paste(canvas, mask=alpha)
            frames.append(rgb)
        # Train one shared palette across entry, hold and exit. No dithering/noise.
        samples = Image.new('RGB', (300, 105*12))
        for k in range(12):
            thumbnail = frames[round(k*(len(frames)-1)/11)].resize((300,105))
            samples.paste(thumbnail,(0,k*105))
        # Reserve the artwork's exact colors. Tiny amber/mint/violet tool strokes
        # otherwise disappear when a gradient-heavy canvas trains the palette.
        anchors=sorted(set(re.findall(r'#[0-9A-Fa-f]{6}',svg.read_text())))
        gradient_colors=255-len(anchors)
        palette = samples.quantize(colors=gradient_colors, method=Image.Quantize.MEDIANCUT)
        pal = palette.getpalette()[:gradient_colors*3]
        pal += [int(color[i:i+2],16) for color in anchors for i in (1,3,5)]
        pal += [255,0,255]
        palette.putpalette(pal)
        transparency = alpha.point(lambda a:255 if a < 128 else 0)
        encoded = []
        for rgb in frames:
            quantized = rgb.quantize(palette=palette, dither=Image.Dither.NONE)
            quantized.paste(255, mask=transparency)
            encoded.append(quantized)
        output = svg.with_suffix('.gif')
        encoded[0].save(output, save_all=True, append_images=encoded[1:],
                        duration=round(1000/spec['fps']), loop=0, transparency=255,
                        disposal=1, optimize=False)
        # Check the encoded animation, including Pillow's merged still frames.
        decoded, timeline, elapsed = [], [], 0
        with Image.open(output) as gif:
            loop = gif.info.get('loop')
            for i in range(gif.n_frames):
                gif.seek(i)
                timeline.append(elapsed)
                decoded.append(gif.convert('RGBA'))
                elapsed += gif.info['duration']
        def at(seconds):
            index = max(i for i,time in enumerate(timeline) if time <= seconds*1000)
            return decoded[index]
        assert elapsed == round(spec['duration']*1000), (output, elapsed)
        assert loop == 0
        assert decoded[0].tobytes() == decoded[-1].tobytes(), 'Loop seam'
        hold_start,hold_end = spec['hold']
        hold = at(hold_start)
        for t in [i/spec['fps'] for i in range(round(hold_start*spec['fps']),round(hold_end*spec['fps']))]:
            assert ImageChops.difference(hold.convert('RGB'),at(t).convert('RGB')).getbbox() is None, 'Hold moved'
        assert ImageChops.difference(at(.04).convert('RGB'),hold.convert('RGB')).getbbox(), 'Missing motion'
        assert output.stat().st_size <= spec['max_size_bytes'], 'Animation exceeds size budget'
        # Keep a static PNG for reliable local review and a contact sheet of motion phases.
        preview = ASSETS/'preview'
        preview.mkdir(exist_ok=True)
        Image.open(tmp/'settled.png').save(preview/f'{svg.stem}.png')
        sheet = Image.new('RGB', (900, 2*(round(300*base_image.height/base_image.width)+32)), '#e6e6e6')
        draw = ImageDraw.Draw(sheet)
        for k,(t,label) in enumerate([(0,'Entry / 0.00s'),(1.2,'Assemble / 1.20s'),(3.0,'Scan / 3.00s'),(5.2,'Hold / 5.20s'),(7.9,'Reset / 7.90s'),(8.72,'Loop / 8.72s')]):
            im = at(t)
            im=im.resize((300,round(300*im.height/im.width)),Image.Resampling.LANCZOS)
            x,y = (k%3)*300,(k//3)*(im.height+32)
            draw.text((x+10,y+8),label,fill='#192129')
            sheet.paste(im,(x,y+32),im)
        sheet.save(preview/f'{svg.stem}-motion.png')
        return {'asset':output.name,'dimensions':list(base_image.size),'bytes':output.stat().st_size,
                'encoded_frames':len(decoded),'source_frames':len(frames),'duration_ms':elapsed,
                'source_fps':spec['fps'],'hold_seconds':hold_end-hold_start,
                'loop_boundary_identical':True,'hold_pixel_still':True,'rounded_corners_transparent': all(f.getpixel((0,0))[3]==0 for f in decoded)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node',default='node')
    args = parser.parse_args()
    spec = json.loads((HERE/'motion.json').read_text())
    results = [render(svg,args.node,spec) for svg in sorted(ASSETS.glob('hero-*.svg'))]
    (ASSETS/'preview'/'motion-checks.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':
    main()
