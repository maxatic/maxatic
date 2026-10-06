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
    """A clearly described decorative calendar; extra accents do not alter source activity."""
    import hashlib
    days=sorted(days,key=lambda d:d['date'])
    first=date.fromisoformat(days[0]['date']);first-=timedelta(days=(first.weekday()+1)%7)
    last=date.fromisoformat(days[-1]['date']);n=(last-first).days//7+1
    if mobile:
        first+=timedelta(weeks=max(0,n-26));days=[d for d in days if date.fromisoformat(d['date'])>=first];n=(last-first).days//7+1
    dark=theme=='dark';bg='#0d1110' if dark else '#f8faf8';fg='#d1dcd3' if dark else '#263f2e';muted='#899b8e' if dark else '#65806d'
    palette=['#15231a','#174d2d','#237e41','#36b859','#64e582'] if dark else ['#e5f2e8','#b9e6c5','#7ecd94','#49b36b','#288b47']
    width=800 if mobile else 1600;height=320;pitch=28;size=21;left=(width-n*pitch+7)/2;top=106
    cells=[];months=[];seen=set();active=0
    for d in days:
        dt=date.fromisoformat(d['date']);col=(dt-first).days//7;row=(dt.weekday()+1)%7
        digest=hashlib.sha256(('maxatic/art/'+d['date']).encode()).digest()
        decorative=d['level']==0 and digest[0]<148
        level=(1+digest[1]%3) if decorative else d['level'];active+=int(level>0)
        x=left+col*pitch;y=top+row*pitch
        label='Decorative green accent; not a recorded contribution' if decorative else f'Actual contribution intensity: {d["level"]} of 4'
        cells.append(f'<rect class="cell" x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="4.5" fill="{palette[level]}" style="animation-delay:{col*.035:.3f}s"><title>{d["date"]}: {label}</title></rect>')
        month=(dt.year,dt.month)
        if month not in seen:
            seen.add(month)
            # The final partial month stays within the artwork boundary.
            label_x=min(width-30,left+col*pitch)
            months.append(f'<text x="{label_x:.1f}" y="86" font-size="18" fill="{muted}">{dt.strftime("%b")}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>maxatic — contribution-inspired artwork</title><desc>Stylized green calendar with actual activity and additional decorative squares. This is an artistic composition, not a representation of contribution counts. Desktop shows the past year; mobile shows the last 26 weeks.</desc><style>.cell{{transform-box:fill-box;transform-origin:center;animation:pop .7s cubic-bezier(.2,.8,.2,1) both}}@keyframes pop{{0%{{opacity:.2;transform:scale(.75)}}70%{{opacity:1;transform:scale(1.08)}}100%{{opacity:1;transform:scale(1)}}}}.sweep{{animation:sweep 18s linear infinite}}@keyframes sweep{{0%,10%{{transform:translateX(-100px);opacity:0}}14%{{opacity:.3}}85%{{transform:translateX({width}px);opacity:.3}}90%,100%{{transform:translateX({width}px);opacity:0}}}}@media(prefers-reduced-motion:reduce){{.cell{{animation:none!important;opacity:1;transform:none}}.sweep{{display:none}}}}</style><defs><clipPath id="calendar"><rect x="{left-2:.1f}" y="{top-2}" width="{n*pitch+2}" height="{7*pitch+2}"/></clipPath><linearGradient id="glow"><stop stop-color="#57d778" stop-opacity="0"/><stop offset=".5" stop-color="#8afaac"/><stop offset="1" stop-color="#57d778" stop-opacity="0"/></linearGradient></defs><rect width="{width}" height="{height}" rx="20" fill="{bg}"/><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="20" fill="none" stroke="{'#2b342e' if dark else '#d5dfd7'}"/><g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"><text x="{left:.1f}" y="42" font-size="22" font-weight="600" fill="{fg}">maxatic</text>{''.join(months)}</g>{''.join(cells)}<g clip-path="url(#calendar)"><rect class="sweep" x="0" y="104" width="90" height="197" fill="url(#glow)" opacity="0"/></g></svg>'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--username',default='maxatic');p.add_argument('--html');p.add_argument('--output',default=str(Path(__file__).resolve().parents[1]/'assets'));a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}',a.username):raise ValueError('Invalid GitHub username')
    html=Path(a.html).read_text() if a.html else urllib.request.urlopen(urllib.request.Request(f'https://github.com/users/{a.username}/contributions',headers={'User-Agent':'maxatic-profile-artwork'}),timeout=30).read().decode()
    c=Calendar();c.feed(html)
    if len(c.days)<300 or len({d['date'] for d in c.days})!=len(c.days):raise ValueError('Unexpected calendar response; preserving existing artwork')
    output=Path(a.output);output.mkdir(parents=True,exist_ok=True)
    for theme in ['light','dark']:
        for mobile in [False,True]:
            file=output/f'contributions-{"mobile-" if mobile else ""}{theme}.svg';art=render(c.days,theme,mobile);file.write_text(art);file.with_name(file.stem+'-static.svg').write_text(art.replace('</style>','</style><style>.cell{animation:none!important;opacity:1!important;transform:none!important}.sweep{display:none!important}</style>'));print(f'Generated {file.name}: {len(c.days)} calendar days')
    (output/'contributions-data.json').write_text(json.dumps({'username':a.username,'days':sorted(c.days,key=lambda d:d['date'])},indent=2)+'\n')

if __name__=='__main__':main()
