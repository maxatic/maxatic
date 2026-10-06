#!/usr/bin/env python3
"""Build personal terminal panels. Only the contribution artwork uses synthetic accents."""
from pathlib import Path
from html import escape
import json, math, xml.etree.ElementTree as E
from PIL import Image, ImageOps, ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
MONO='ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
THEMES={'dark':{'bg':'#0d1110','raised':'#141a17','line':'#2b342e','fg':'#e1e7e2','muted':'#8b998e','green':'#57d778'},'light':{'bg':'#f8faf8','raised':'#eef3ef','line':'#d5dfd7','fg':'#18291d','muted':'#62776a','green':'#2e914b'}}

def shell(c,title,w=840,h=950):
    return f'<rect width="{w}" height="{h}" rx="20" fill="{c["bg"]}"/><rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="20" fill="none" stroke="{c["line"]}"/><path d="M0 46H{w}" stroke="{c["line"]}"/><circle cx="24" cy="23" r="5" fill="{c["muted"]}" opacity=".4"/><circle cx="42" cy="23" r="5" fill="{c["muted"]}" opacity=".65"/><circle cx="60" cy="23" r="5" fill="{c["green"]}"/><text x="{w/2}" y="29" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{c["muted"]}">{escape(title)}</text>'

def portrait(photo,theme,static=False):
    c=THEMES[theme];im=Image.open(photo).convert('L');w,h=im.size
    side=min(w,h);top=min(h-side,int(h*.06));left=(w-side)//2;im=im.crop((left,top,left+side,top+side))
    im=ImageOps.autocontrast(im,cutoff=1);im=ImageEnhance.Brightness(im).enhance(1.08)
    cols=140;rows=94;im=im.resize((cols,rows),Image.Resampling.LANCZOS)
    ramp=' .,:;=+*#%@';lines=[]
    for y in range(rows):
        line=''.join(ramp[min(len(ramp)-1,int(((255-im.getpixel((x,y)))/255)**.67*(len(ramp)-1)))] for x in range(cols));lines.append(line)
    (ROOT/'source/portrait.txt').write_text('\n'.join(lines)+'\n')
    text=[];styles=[];defs=[];x=28;width=784;top=114;pitch=8.4
    for i,line in enumerate(lines):
        start=2+i*.031;end=start+.031
        a=start/18*100;b=end/18*100
        styles.append(f'@keyframes row{i}{{0%,{a:.4f}%{{width:0}}{b:.4f}%,94%{{width:{width}px}}98%,100%{{width:0}}}}')
        animation='' if static else f' style="animation:row{i} 18s linear infinite"'
        defs.append(f'<clipPath id="row{i}"><rect class="reveal" x="{x}" y="{top+i*pitch-7}" width="{width}" height="{pitch+1}"{animation}/></clipPath>')
        text.append(f'<text xml:space="preserve" x="{x}" y="{top+i*pitch:.2f}" fill="{c["fg"]}" font-family="{MONO}" font-size="8.5" textLength="{width}" lengthAdjust="spacing" clip-path="url(#row{i})">{escape(line)}</text>')
    motion='' if static else ''.join(styles)+f'.scan{{animation:scan 18s linear infinite}}@keyframes scan{{0%,11%{{transform:translateY(0);opacity:0}}12%{{opacity:.7}}29%{{transform:translateY(782px);opacity:.7}}30%,100%{{transform:translateY(782px);opacity:0}}}}.caret{{animation:blink 1.2s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}'
    css=motion+f'@media(prefers-reduced-motion:reduce){{.reveal{{animation:none!important;width:{width}px!important}}.scan{{display:none}}.caret{{animation:none}}}}'
    scan='' if static else f'<rect class="scan" x="28" y="105" width="784" height="1" fill="{c["green"]}" opacity="0"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="950" viewBox="0 0 840 950"><title>Maxat — ASCII portrait</title><desc>An ASCII rendering of Maxat’s original portrait. Characters type across each row, then hold before repeating.</desc><style>{css}</style><defs>{"".join(defs)}</defs>{shell(c,"maxatic / portrait")}<text x="28" y="86" font-family="{MONO}" font-size="20" fill="{c["green"]}">maxatic ~ $ whoami</text><rect class="caret" x="280" y="69" width="11" height="21" fill="{c["green"]}"/>{"".join(text)}{scan}<path d="M28 918H812" stroke="{c["line"]}"/><text x="28" y="939" font-family="{MONO}" font-size="12" fill="{c["muted"]}">product · design · code</text></svg>'

def load_icons():
    return json.loads((ROOT/'source/icons.json').read_text())

def profile(theme,static=False):
    c=THEMES[theme];data=json.loads((ROOT/'source/profile.json').read_text());icons=load_icons();pieces=[]
    def text(x,y,value,size=20,color=None,weight=None):
        return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{color or c["fg"]}"'+(f' font-weight="{weight}"' if weight else '')+f'>{escape(value)}</text>'
    def group(content,delay):
        return '<g'+('' if static else f' class="section" style="animation-delay:{delay}s"')+'>'+content+'</g>'
    pieces.append(group(text(34,110,data['name'],52,weight='600')+text(34,150,'Product × AI × Design',23,c['muted']),.15))
    focus=text(34,208,'SPECIALIZATION',16,c['green'])
    for i,t in enumerate(data['specialization']):focus+=text(34,248+i*34,t,22)
    pieces.append(group(focus,.3))
    experience=f'<path d="M34 339H806" stroke="{c["line"]}"/>'+text(34,378,'EXPERIENCE',16,c['green'])
    for i,company in enumerate(data['companies']):
        y=415+i*52
        if company=='Red Hat':icon=f'<g transform="translate(34 {y-25}) scale(1.35)" fill="{c["fg"]}">{icons["redhat"]}</g>'
        elif company=='Amazon':icon=f'<path d="M36 {y-7}q16 14 35 0m-5-2 5 2-2 5" fill="none" stroke="{c["fg"]}" stroke-width="3" stroke-linecap="round"/>'
        else:icon=f'<g stroke="{c["fg"]}" stroke-width="3.4" fill="none"><path d="m35 {y-22} 8 17 8-17m5 0h12m-12 8h10m-10 9h12"/></g>'
        experience+=icon+text(88,y,company,25)
    pieces.append(group(experience,.45))
    stack=f'<path d="M34 558H806" stroke="{c["line"]}"/>'+text(34,598,'STACK',16,c['green'])
    icon_ids={'TypeScript':'typescript','Figma':'figma','Framer':'framer','Claude Code':'claude','Python':'python','Go':'go','Git':'git'}
    for i,name in enumerate(data['stack']):
        col=i%3;row=i//3;x=34+col*264;y=629+row*83
        stack+=f'<rect x="{x}" y="{y}" width="244" height="67" rx="12" fill="{c["raised"]}" stroke="{c["line"]}"/><g transform="translate({x+16} {y+19}) scale(1.18)" fill="{c["fg"]}">{icons[icon_ids[name]]}</g>'+text(x+57,y+42,name,18 if name=='Claude Code' else 20)
    pieces.append(group(stack,.6))
    pieces.append(group(text(34,829,'AI agents / MCP',20,c['muted'])+text(34,861,'Rapid prototyping / product discovery',17,c['muted']),.75))
    css='' if static else '.section{animation:appear .7s cubic-bezier(.2,.8,.2,1) both}@keyframes appear{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="950" viewBox="0 0 840 950"><title>Maxat — profile and stack</title><desc>Product management, AI, data-driven products, design and prototyping. Experience and technology details.</desc><style>{css}@media(prefers-reduced-motion:reduce){{.section{{animation:none!important;opacity:1;transform:none}}}}</style>{shell(c,"maxatic / profile")}{"".join(pieces)}<path d="M28 918H812" stroke="{c["line"]}"/>{text(34,939,'maxat.live ↗',13,c['muted'])}</svg>'

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--photo',required=True);a=p.parse_args()
    for theme in THEMES:
        for static in [False,True]:
            suffix='-static' if static else ''
            for kind,art in [('portrait',portrait(a.photo,theme,static)),('profile',profile(theme,static))]:
                file=ROOT/'assets'/f'{kind}-{theme}{suffix}.svg';file.write_text(art);E.parse(file);print('Built',file.name)

if __name__=='__main__':main()
