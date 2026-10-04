#!/usr/bin/env python3
"""Generate self-contained animated SVGs from a public GitHub contribution calendar."""
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
import argparse, json, re, urllib.request

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__(); self.days=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='td' and 'ContributionCalendar-day' in a.get('class','') and a.get('data-date'):
            self.days.append({'date':a['data-date'],'level':int(a['data-level'])})

def render(days, theme, mobile=False):
    days=sorted(days,key=lambda d:d['date'])
    first=date.fromisoformat(days[0]['date']); first-=timedelta(days=(first.weekday()+1)%7)
    last=date.fromisoformat(days[-1]['date']); n=(last-first).days//7+1
    if mobile:
        first+=timedelta(weeks=max(0,n-26)); days=[d for d in days if date.fromisoformat(d['date'])>=first];n=(last-first).days//7+1
    palette=['#e8e8ec','#c9c9cf','#96969e','#62626b','#252529'] if theme=='light' else ['#29292e','#494950','#71717b','#a8a8b1','#efeff2']
    bg='#f5f5f7' if theme=='light' else '#19191c';ink='#1d1d1f' if theme=='light' else '#f5f5f7';muted='#727276' if theme=='light' else '#a4a4aa'
    w=800 if mobile else 1600;h=440;pitch=27 if mobile else 28;cell=20;left=(w-n*pitch+7)/2;top=166
    total=len(days);duration=48;travel=44;frames=[];positions={};valid={date.fromisoformat(d['date']) for d in days};i=0
    for c in range(n):
        for step in range(7):
            r=step if c%2==0 else 6-step
            if first+timedelta(days=c*7+r) not in valid:continue
            x=left+c*pitch;y=top+r*pitch
            positions[(c,r)]=(i,x,y);frames.append(f'{i/total*travel/duration*100:.4f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}');i+=1
    _,x,y=max(positions.values(),key=lambda p:p[0])
    frames.extend([f'{travel/duration*100:.4f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}',f'94%{{transform:translate({x:.1f}px,376px);opacity:0}}',f'98%{{transform:translate({left:.1f}px,140px);opacity:0}}',f'100%{{transform:translate({left:.1f}px,166px);opacity:1}}'])
    cells=[];months=[];seen=set()
    for d in days:
        dt=date.fromisoformat(d['date']);c=(dt-first).days//7;r=(dt.weekday()+1)%7;i,x,y=positions[(c,r)];level=d['level'];color=palette[level]
        cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="5" fill="{color}"><title>{d["date"]}: contribution intensity {level} of 4</title></rect>')
        if level:
            delay=i/total*travel
            cells.append(f'<rect class="spark" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="5" fill="{ink}" style="animation-delay:{delay:.3f}s"/>')
        month=(dt.year,dt.month)
        if month not in seen:
            seen.add(month);months.append(f'<text x="{left+c*pitch:.1f}" y="144" font-size="16" fill="{muted}">{dt.strftime("%b")}</text>')
    period=f'{first.strftime("%b %Y")} — {last.strftime("%b %Y")}'
    label='LAST 26 WEEKS' if mobile else 'A YEAR OF SMALL MOVES'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>Maxat's contribution journey</title><desc>Actual public GitHub contribution intensity, {first} through {last}. A small monogram visits each calendar square and gently illuminates active days.</desc><style>
    .traveler{{animation:journey {duration}s linear infinite}}.spark{{opacity:0;animation:ignite {duration}s linear infinite}}
    @keyframes journey{{{''.join(frames)}}}@keyframes ignite{{0%{{opacity:0}}.12%,.8%{{opacity:.8}}2.5%,100%{{opacity:0}}}}
    @media(prefers-reduced-motion:reduce){{.traveler{{display:none}}.spark{{animation:none;opacity:0}}}}
    </style><rect width="{w}" height="{h}" rx="28" fill="{bg}"/><g font-family="Helvetica Neue,Arial,sans-serif"><text x="44" y="57" fill="{muted}" font-size="{'16' if mobile else '18'}" letter-spacing="2">{label}</text><text x="44" y="98" fill="{ink}" font-size="32" font-weight="600" letter-spacing="-1">One small move. Then another.</text><text x="{w-44}" y="57" fill="{muted}" font-size="14" text-anchor="end">{period}</text>{''.join(months)}{''.join(cells)}<g class="traveler" transform="translate({left:.1f} 166)"><rect x="-4" y="-4" width="28" height="28" rx="9" fill="{ink}" opacity=".13"/><rect width="20" height="20" rx="6" fill="{ink}"/><text x="10" y="14.5" text-anchor="middle" fill="{bg}" font-size="16" font-weight="600">m</text></g><text x="44" y="405" fill="{muted}" font-size="16">Real activity. A little creative license.</text><text x="{w-44}" y="405" text-anchor="end" fill="{muted}" font-size="14">maxatic / building in public</text></g></svg>'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--username',default='maxatic');p.add_argument('--html');p.add_argument('--output',default=str(Path(__file__).resolve().parents[1]/'assets'));a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}',a.username):raise ValueError('Invalid GitHub username')
    html=Path(a.html).read_text() if a.html else urllib.request.urlopen(urllib.request.Request(f'https://github.com/users/{a.username}/contributions',headers={'User-Agent':'maxatic-profile-artwork'}),timeout=30).read().decode()
    c=Calendar();c.feed(html)
    if len(c.days)<300 or len({d['date'] for d in c.days})!=len(c.days):raise ValueError('Unexpected calendar response; preserving existing artwork')
    output=Path(a.output);output.mkdir(parents=True,exist_ok=True)
    for theme in ['light','dark']:
        for mobile in [False,True]:
            file=output/f'contributions-{"mobile-" if mobile else ""}{theme}.svg';art=render(c.days,theme,mobile);file.write_text(art);file.with_name(file.stem+'-static.svg').write_text(art.replace('</style>','</style><style>.traveler{display:none!important}.spark{animation:none!important;opacity:0!important}</style>'));print(f'Generated {file.name}: {len(c.days)} calendar days')
    (output/'contributions-data.json').write_text(json.dumps({'username':a.username,'days':sorted(c.days,key=lambda d:d['date'])},indent=2)+'\n')

if __name__=='__main__':main()
