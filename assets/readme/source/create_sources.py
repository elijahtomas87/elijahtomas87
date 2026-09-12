#!/usr/bin/env python3
"""Editable vector scene: isometric ET sculpture, workshop tools and terminal."""
from pathlib import Path
import argparse
import json
from html import escape

ASSETS=Path(__file__).resolve().parents[1]
PALETTES={
 'dark':{'bg':'#140F20','fg':'#F6F0FF','muted':'#BEAFD2','line':'#443453','primary':'#C49AFF','amber':'#F2BE77','teal':'#71D3C7','lavender':'#DED0FF','amethyst':'#BCA8F3','surface':'#2A1F3E','edge':'#1D152C','grid':'#3A2A4D'},
 'light':{'bg':'#F5F0FA','fg':'#2C173F','muted':'#695278','line':'#D1BEE1','primary':'#7840B7','amber':'#8B5719','teal':'#166B65','lavender':'#795DA3','amethyst':'#71529E','surface':'#E5D6EF','edge':'#CBB4DE','grid':'#DFD0E9'}
}
SANS="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO="ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"

def text(x,y,size,value,color,extra=''):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(value)}</text>'

def icon_art(kind,color='#DEC6F5'):
 """Original small workshop instruments, built from purpose-specific geometry."""
 shapes={
  'draft': '<path d="M13 13H37L46 22V49H13Z" fill="currentColor" fill-opacity=".12"/><path d="M13 13H37L46 22V49H13Z M36 13V23H46 M19 23H29 M19 30H31 M19 37H25"/><path d="M28 44L31 35L47 15L52 19L36 40Z" fill="currentColor" fill-opacity=".32"/><path d="M31 35L36 40 M43 20L48 24 M28 44L36 40"/><circle cx="20" cy="43" r="1.6" fill="currentColor" stroke="none"/>',
  'assemble': '<path d="M10 33L24 26L38 33L24 41Z M24 41V53L10 45V33 M24 53L38 45V33" fill="currentColor" fill-opacity=".16"/><path d="M28 33L42 26L56 33L42 41Z M42 41V53L28 45V33 M42 53L56 45V33" fill="currentColor" fill-opacity=".3"/><path d="M20 13L34 6L48 13L34 21Z M34 21V33L20 25V13 M34 33L48 25V13" fill="currentColor" fill-opacity=".5"/><path d="M34 21V33"/>',
  'inspect': '<path d="M11 15H53V23H11Z" fill="currentColor" fill-opacity=".28"/><path d="M17 23V48H24V38 M46 23V48H39V38"/><path d="M24 30H39V43H24Z" fill="currentColor" fill-opacity=".4"/><path d="M24 30L29 26H44V39L39 43 M39 30L44 26 M29 26V21 M17 16V20 M23 16V19 M29 16V20 M35 16V19 M41 16V20 M47 16V19"/><path d="M17 52H46" stroke-opacity=".45"/>',
  'projects': '<path d="M10 37L32 26L54 37L32 49Z" fill="currentColor" fill-opacity=".12"/><path d="M10 29L32 18L54 29L32 41Z" fill="currentColor" fill-opacity=".24"/><path d="M10 21L32 10L54 21L32 33Z" fill="currentColor" fill-opacity=".45"/><path d="M19 21L32 15L45 21 M32 33V38 M32 42V47"/>',
  'ledger': '<path d="M12 12H45L51 18V51H12Z" fill="currentColor" fill-opacity=".15"/><path d="M20 12V51 M44 12V20H51 M26 25H44 M26 32H33 M38 32H44 M26 39H33 M38 39H44 M26 46H44"/><path d="M8 18H15 M8 29H15 M8 40H15"/><path d="M22 14H42V19H22Z" fill="currentColor" stroke="none" fill-opacity=".36"/>',
  'publishing': '<path d="M8 20H24V44H8Z" fill="currentColor" fill-opacity=".25"/><path d="M12 27H20 M12 33H18 M24 32H33 M33 15V49 M33 15H40 M33 32H40 M33 49H40"/><path d="M40 8H56V22H40Z M40 25H56V39H40Z M40 42H56V56H40Z" fill="currentColor" fill-opacity=".17"/><path d="M45 13H51 M45 17H49 M45 30L51 33L45 36Z M45 47H51 M45 51H49"/>',
  'reasoning': '<path d="M10 10H25V24H10Z M39 10H54V24H39Z M25 40H40V54H25Z" fill="currentColor" fill-opacity=".23"/><path d="M17.5 24V31H32 M46.5 24V31H32 M32 31V40 M14 15H21 M14 19H19 M43 15H50 M43 19H48 M29 45H36 M29 49H34"/><path d="M28 27L32 23L36 27L32 31Z" fill="currentColor" fill-opacity=".65"/>',
  'baseball': '<path d="M18 12V53" stroke-width="3"/><path d="M20 15L52 22L20 32Z" fill="#DAC0F0" stroke="#EAD8FA" stroke-width="2"/><path d="M20 15L28 21L20 32Z" fill="#9467B9" stroke="none"/><path d="M14 53H23" stroke-width="2.6"/><circle cx="42" cy="44" r="11" fill="#EDE0F8" stroke="#F8F0FF" stroke-width="2"/><path d="M37 35Q44 44 37 53 M47 35Q40 44 47 53" stroke="#80509F" stroke-width="1.8"/>',
  'process': '<path d="M20 45Q32 55 44 45" stroke="#795690" stroke-width="2"/><path d="M28 24L33 27L21 51L16 55L18 48Z" fill="#D5B9EB" stroke="#EDDBFA" stroke-width="1.8"/><path d="M36 24L31 27L43 49L48 53L46 46Z" fill="#AD84CC" stroke="#D9BCEC" stroke-width="1.8"/><path d="M24 36H40" stroke-width="2.4"/><path d="M30 8H34V14H30Z" fill="#E5D1F5" stroke="none"/><circle cx="32" cy="20" r="7" fill="#68458A" stroke="#E6D0F7" stroke-width="2.4"/><circle cx="32" cy="20" r="2.1" fill="#F7EEFF" stroke="none"/><rect x="30" y="33.5" width="4" height="5" rx="1" fill="#E5D1F5" stroke="none"/>'
 }
 # Accents have specific roles: amber for drafting/annotation, teal for checks.
 # Keep the accepted silhouettes and the majority of each emblem lavender.
 if kind=='baseball':
  shapes[kind]=shapes[kind].replace('fill="#9467B9"','fill="#F2BE77"')
 if kind=='process':
  shapes[kind]=shapes[kind].replace('fill="#F7EEFF"','fill="#71D3C7"').replace('fill="#E5D1F5"','fill="#F2BE77"')
 if kind=='ledger':
  shapes[kind]=shapes[kind].replace('M22 14H42V19H22Z" fill="currentColor" stroke="none" fill-opacity=".36"','M22 14H42V19H22Z" fill="#F2BE77" stroke="none"')
 if kind=='reasoning':
  shapes[kind]=shapes[kind].replace('M28 27L32 23L36 27L32 31Z" fill="currentColor" fill-opacity=".65"','M28 27L32 23L36 27L32 31Z" fill="#71D3C7" stroke="#71D3C7"')
 return f'<g color="{color}" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none">{shapes[kind]}</g>'

def icon(kind,color='#DEC6F5',size=64):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64" role="img" aria-labelledby="title desc"><title id="title">{kind.title()} workshop emblem</title><desc id="desc">Original layered vector artwork representing {kind}.</desc><rect x="1" y="1" width="62" height="62" rx="14" fill="#21162F" stroke="#5B4073"/>{icon_art(kind,color)}</svg>'

def scene(theme,compact=False):
 c=PALETTES[theme]; dark=theme=='dark'
 W,H=(720,1010) if compact else (1200,680)
 cx,cy,scale=(384,408,.94) if compact else (874,290,1)
 def p(x,y,z=0):return (cx+(x-y)*.82*scale,cy+(x+y)*.405*scale-z*scale)
 def pts(vertices,z=0):return ' '.join(f'{a:.2f},{b:.2f}' for a,b in [p(x,y,z) for x,y in vertices])
 def poly(vertices,fill,z=0,extra=''):return f'<polygon points="{pts(vertices,z)}" fill="{fill}" {extra}/>'
 def prism(vertices,z,depth,top,side1,side2):
  out=[]
  # Every side is included, top face covers the back faces. Visible faces get directional color.
  for a,b in zip(vertices,vertices[1:]+vertices[:1]):
   coords=[p(*a,z),p(*b,z),p(*b,z-depth),p(*a,z-depth)]
   color=side1 if b[0]!=a[0] else side2
   out.append(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in coords)}" fill="{color}"/>')
  out.append(poly(vertices,top,z,extra='stroke="#DCC5EC" stroke-opacity=".18" stroke-width="1"'))
  return ''.join(out)
 def pathworld(vertices,z=0,stroke=None,extra=''):
  coordinates=[p(x,y,z) for x,y in vertices]
  d='M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in coordinates)
  weight='' if 'stroke-width' in extra else 'stroke-width="1.2"'
  return f'<path d="{d}" fill="none" stroke="{stroke or c["line"]}" {weight} {extra}/>'
 out=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
 <title id="title">Elijah Tomas — The digital workshop</title>
 <desc id="desc">Elijah Tomas. Ideas into systems. A purple ET monogram assembles on an isometric workbench. Amber marks drafting tools; teal marks inspection. A terminal types the name and the sequence design, code, test.</desc>
 <defs>
  <linearGradient id="backdrop" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['bg']}"/><stop offset="1" stop-color="{'#261633' if dark else '#EEE4F5'}"/></linearGradient>
  <radialGradient id="atmosphere"><stop stop-color="{'#8E52B6' if dark else '#D8B5EF'}" stop-opacity=".29"/><stop offset="1" stop-color="{c['bg']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="ceramic" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFF8FF"/><stop offset="1" stop-color="#D7C2E7"/></linearGradient>
  <linearGradient id="enamel" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#EFD8FF"/><stop offset=".5" stop-color="#CA98F1"/><stop offset="1" stop-color="#9D64CE"/></linearGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{c['surface']}"/><stop offset="1" stop-color="{'#3E2B51' if dark else '#F0E5F7'}"/></linearGradient>
 </defs>
 <rect width="{W}" height="{H}" rx="24" fill="url(#backdrop)"/>
 <ellipse cx="{cx}" cy="{cy+75}" rx="{340*scale}" ry="{330*scale}" fill="url(#atmosphere)"/>
 <g font-family="{SANS}">''']
 # Fine edge frame, with interruptions at the corners, more instrument than card.
 out.append(f'<path d="M24 82V40Q24 24 40 24H82 M{W-82} 24H{W-40}Q{W-24} 24 {W-24} 40V82 M24 {H-82}V{H-40}Q24 {H-24} 40 {H-24}H82 M{W-82} {H-24}H{W-40}Q{W-24} {H-24} {W-24} {H-40}V{H-82}" fill="none" stroke="{c["line"]}"/>')
 # Identity remains visible throughout the animation.
 x=42 if compact else 56
 out.append(f'<g id="identity"><g font-family="{MONO}">')
 out.append(text(x,63,18 if compact else 19,'THE DIGITAL WORKSHOP',c['muted'],'letter-spacing="3"'))
 out.append('</g>')
 if not compact:
  out.append(f'<g font-family="{MONO}">{text(703,143,18,"ET / ASSEMBLY STUDY",c["muted"],"letter-spacing=\"1.4\"")}</g>')
 if compact:
  out.append(text(x,154,78,'Elijah Tomas',c['fg'],'font-weight="750" letter-spacing="-4.8"'))
  out.append(text(x,212,37,'Ideas into systems.',c['muted'],'letter-spacing="-1"'))
 else:
  out.append(text(x,178,112,'Elijah',c['fg'],'font-weight="750" letter-spacing="-6"'))
  out.append(text(x,283,112,'Tomas',c['fg'],'font-weight="750" letter-spacing="-6"'))
  out.append(text(x+3,340,35,'Ideas into systems.',c['muted'],'letter-spacing="-.8"'))
 out.append('</g>')
 # A faint footprint anchors the object to a real spatial scene.
 out.append(poly([(-24,-24),(322,-24),(322,322),(-24,322)],'#0C0714' if dark else '#C2ADD3',-31,extra='opacity=".24"'))
 out.append('<g id="bench">')
 out.append(prism([(-10,-10),(302,-10),(302,302),(-10,302)],0,24,'url(#floor)',c['edge'],'#342343' if dark else '#D3BCE5'))
 # Small machining/routing lines are restricted to the workbench surface.
 for i in range(30,301,45):
  out.append(pathworld([(i,0),(i,292)],.5,c['line'],extra='opacity=".46"'))
  out.append(pathworld([(0,i),(292,i)],.5,c['line'],extra='opacity=".46"'))
 out.append(pathworld([(8,278),(278,278),(278,12)],1,c['primary'],extra='opacity=".5"'))
 out.append('</g>')
 # Routing connects specific tools rather than filling the background with arbitrary circuits.
 routes=[[(0,215),(-50,215),(-50,110),(-116,110)],[(226,0),(226,-52),(110,-52),(110,-132)],[(292,152),(352,152),(352,75),(385,75)]]
 out.append('<g id="routes">')
 for route,col in zip(routes,[c['primary'],c['amber'],c['teal']]):
  out.append(pathworld(route,4,col,extra='stroke-width="2.5" stroke-dasharray="5 6"'))
 out.append('</g>')
 E=[(24,30),(120,30),(120,64),(58,64),(58,100),(108,100),(108,132),(58,132),(58,172),(120,172),(120,206),(24,206)]
 TC=[(144,30),(272,30),(272,64),(144,64)]
 TS=[(191,64),(225,64),(225,206),(191,206)]
 for shape in [E,TC,TS]:out.append(poly(shape,'none',2,extra=f'stroke="{c["primary"]}" stroke-opacity=".55" stroke-dasharray="3 5"'))
 # One custom letter and two interlocking T components, with directional side faces.
 out.append('<g id="letter-e">'+prism(E,61,42,'url(#ceramic)','#A28AB8','#685078')+'</g>')
 out.append('<g id="letter-t-stem">'+prism(TS,61,42,'url(#enamel)','#9B62BC','#63377F')+'</g>')
 out.append('<g id="letter-t-cap">'+prism(TC,61,42,'url(#enamel)','#9B62BC','#63377F')+'</g>')
 # Front-edge sockets light up after assembly, no fabricated measurements or live status.
 out.append('<g id="sockets">')
 for a,color in [(56,c['primary']),(144,c['amber']),(232,c['teal'])]:
  out.append(pathworld([(a,302),(a+35,302)],-11,color,extra='stroke-width="4" stroke-linecap="round"'))
 out.append('</g>')
 # Floating tool tiles, with specific symbols and soft extruded bodies.
 tiles=[('idea',(106,-114),'draft',c['amber'],-9),('code',(-108,110),'assemble',c['primary'],8),('refine',(374,72),'inspect',c['teal'],-6)]
 for key,(wx,wy),kind,color,angle in tiles:
  px,py=p(wx,wy,35)
  out.append(f'<g id="tool-{key}" transform="translate({px:.1f} {py:.1f}) rotate({angle})"><rect x="-43" y="-35" width="88" height="88" rx="19" fill="#10081A" opacity=".3"/><rect x="-44" y="-44" width="88" height="88" rx="18" fill="{c["edge"]}" stroke="{c["line"]}"/><path d="M-26 -35H26" stroke="{color}" stroke-opacity=".7"/><g transform="translate(-30 -30) scale(.94)">')
  out.append(icon_art(kind,color)+'</g></g>')
 # A sweep exists only in the animation; the source SVG always shows the settled state.
 sx,sy=p(-10,146,72)
 mask_points=[p(0,0,90),p(302,0,90),p(302,0,-25),p(302,302,-25),p(0,302,-25),p(0,302,90)]
 out.append(f'<g id="scan-mask" opacity="0" data-motion-only="true"><polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a,b in mask_points)}" fill="white"/></g>')
 out.append(f'<g id="scan" opacity="0" data-motion-only="true"><path d="M{sx-40:.1f} {cy-110:.1f}V{cy+290:.1f}" stroke="{c["teal"]}" stroke-width="3"/><path d="M{sx-45:.1f} {cy-110:.1f}V{cy+290:.1f}" stroke="{c["teal"]}" stroke-width="13" opacity=".12"/></g>')
 # Workshop caption supports the physical object, without pretending to be telemetry.
 caption_y=708 if compact else 604
 out.append(f'<g font-family="{MONO}">{text(216 if compact else 726,caption_y,18,"DRAFT / ASSEMBLE / INSPECT",c["muted"],"letter-spacing=\"1.2\"")}</g>')
 # Small framed terminal, dark in both themes for a coherent tool identity.
 tx,ty,tw,th=(42,748,636,206) if compact else (56,389,514,221)
 out.append(f'<g id="terminal" font-family="{MONO}"><rect x="{tx+5}" y="{ty+9}" width="{tw}" height="{th}" rx="14" fill="#10081A" opacity=".25"/><rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="14" fill="#170F24" stroke="#59406D"/><path d="M{tx} {ty+43}H{tx+tw}" stroke="#3D2B50"/>')
 for k,col in enumerate(['#F2BE77','#C29BEA','#71D3C7']):out.append(f'<circle cx="{tx+22+k*18}" cy="{ty+22}" r="4" fill="{col}"/>')
 out.append(text(tx+90,ty+28,15,'elijah@local : ~','#BDA7D5'))
 fs=24 if compact else 21
 y1=ty+82;y2=ty+120;y3=ty+163
 out.append(text(tx+22,y1,fs,'❯','#D7B4F8'))
 out.append(f'<g id="terminal-command">{text(tx+49,y1,fs,"whoami", "#EBDDFC")}</g>')
 out.append(f'<g id="terminal-name">{text(tx+22,y2,fs,"Elijah Tomas", "#EBDDFC")}</g>')
 out.append(f'<g id="terminal-process">{text(tx+22,y3,fs-2,"design → code → test", "#BDA7D5")}</g>')
 out.append(f'<g id="terminal-cursor"><rect x="{tx+22}" y="{ty+th-26}" width="9" height="3" fill="#71D3C7"/></g></g>')
 # Quiet footer closes the scene like a maker's plate, not a status dashboard.
 out.append(f'<g font-family="{MONO}">{text(42 if compact else 56,H-31,15,"SOFTWARE / DESIGN / DATA",c["muted"],"letter-spacing=\"1.1\"")}</g>')
 out.append('</g></svg>\n')
 return '\n'.join(out)

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--icons-only',action='store_true')
 args=parser.parse_args()
 for kind in ['draft','assemble','inspect','projects','ledger','publishing','reasoning','baseball','process']:
  (ASSETS/f'icon-{kind}.svg').write_text(icon(kind))
 if args.icons_only:
  print('Built original icon family; hero sources and exports preserved.')
  return
 for theme in PALETTES:
  for compact in [False,True]:
   name=f'hero-{theme}'+('-compact' if compact else '')
   (ASSETS/f'{name}.svg').write_text(scene(theme,compact))
 # One narrative loop: lay the tools out, assemble the sculpture, scan, type, hold.
 layers=[
 {'id':'routes','start':.16,'end':1.7,'reveal':'x'},
 {'id':'tool-idea','start':.12,'end':1.15,'from':[16,-42]},
 {'id':'tool-code','start':.35,'end':1.35,'from':[-40,-22]},
 {'id':'tool-refine','start':.6,'end':1.6,'from':[36,26]},
 {'id':'letter-e','start':.35,'end':1.5,'from':[-36,-58]},
 {'id':'letter-t-stem','start':.9,'end':2.05,'from':[28,-64]},
 {'id':'letter-t-cap','start':1.3,'end':2.45,'from':[28,-78]},
 {'id':'scan','start':2.35,'end':2.55,'from':[0,0],'drift':[360,0], 'drift_time':[2.45,4.0],'exit':[3.8,4.1],'mask':'scan-mask'},
 {'id':'sockets','start':3.3,'end':4.15,'reveal':'x'},
 {'id':'terminal-command','start':.35,'end':1.2,'reveal':'x','steps':6},
 {'id':'terminal-name','start':1.5,'end':2.65,'reveal':'x','steps':12},
 {'id':'terminal-process','start':2.9,'end':4.35,'reveal':'x','steps':19},
 {'id':'terminal-cursor','start':4.35,'end':4.55,'from':[0,0]}
 ]
 spec={'fps':20,'duration':8.8,'colors':256,'max_size_bytes':4_000_000,'hold':[4.6,7.35],'exit':[7.35,8.48],'layers':layers}
 (ASSETS/'source/motion.json').write_text(json.dumps(spec,indent=2)+'\n')
 (ASSETS/'source/palette.json').write_text(json.dumps(PALETTES,indent=2)+'\n')
 print('Built purple workshop scenes, original icon family and layered motion spec.')

if __name__=='__main__':main()
