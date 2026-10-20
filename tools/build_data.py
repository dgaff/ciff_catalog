"""Build the catalog data embedded in index.html from Points North's films_archive.json.

    curl -o films_archive.json https://ciffwebsiteimages.s3.amazonaws.com/films_archive.json
    python3 tools/build_data.py films_archive.json --update-html

Without --update-html the cleaned JSON is written to films.json for inspection.
With it, the active <script id="films-data"> block in index.html is wrapped in an
HTML comment (kept for reference) and the new block is inserted right after it.
"""
import argparse, collections, datetime, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

# Only unambiguous aliases. Indigenous nations etc. are deliberate source entries; leave them.
COUNTRY_ALIAS = {
    'USA': 'United States', 'UK': 'United Kingdom', 'México': 'Mexico',
    'The Netherlands': 'Netherlands', 'Netherland': 'Netherlands',
    'Russian Federation': 'Russia', 'Republic Czech': 'Czech Republic',
    'Congo, Democratic Republic of': 'Democratic Republic of Congo',
}

# Streaming link domain -> platform name. Anything not listed is "Other".
PLATFORMS = {
    'vimeo.com': 'Vimeo', 'youtube.com': 'YouTube', 'youtu.be': 'YouTube',
    'amazon.com': 'Amazon', 'amazon.co.uk': 'Amazon', 'itunes.apple.com': 'iTunes',
    'tv.apple.com': 'Apple TV', 'kanopy.com': 'Kanopy', 'kanopystreaming.com': 'Kanopy',
    'nytimes.com': 'New York Times', 'dafilms.com': 'DAFilms', 'americas.dafilms.com': 'DAFilms',
    'dafilms.pl': 'DAFilms', 'pbs.org': 'PBS', 'oculus.com': 'Meta Quest',
    'play.google.com': 'Google Play', 'netflix.com': 'Netflix', 'store.steampowered.com': 'Steam',
    'tubitv.com': 'Tubi', 'vudu.com': 'Vudu', 'theatlantic.com': 'The Atlantic', 'aeon.co': 'Aeon',
    'sho.com': 'Showtime', 'justwatch.com': 'JustWatch', 'filminlatino.mx': 'Filmin',
    'filmin.es': 'Filmin', 'nfb.ca': 'NFB', 'docplus.com': 'DOCUMENTARY+',
    'cultureunplugged.com': 'Culture Unplugged', 'hulu.com': 'Hulu', 'newyorker.com': 'New Yorker',
    'fandangonow.com': 'Fandango', 'mubi.com': 'MUBI', 'criterionchannel.com': 'Criterion',
}

EDITOR_SPLIT = r'\s*(?:[,;/&]|\band\b)\s*'
DIRECTOR_SPLIT = r'\s*(?:[,&]|\band\b)\s*'  # only used when the linked filmmakers list is empty


def ws(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def split(s, pat=r'\s*,\s*'):
    return [ws(x) for x in re.split(pat, s or '') if x.strip()]


def domain(u):
    h = urlparse(u.strip()).netloc.lower()
    return h[4:] if h.startswith('www.') else h


def website(u):
    u = (u or '').strip()
    return u if not u or re.match(r'https?://', u, re.I) else 'https://' + u


def convert(r):
    f = r['fields']
    trt = f.get('TRT')  # seconds; the source's runtime_str is h:mm, which reads as seconds
    languages = [l.rstrip('.').title()
                 for l in split(f.get('*Languages (if other than English)*'), r'\s*[,;/]\s*')
                 if l.lower() not in ('n', 'a', 'n/a')]
    return {
        'id': r['id'],
        'slug': r['slug'],
        'title': ws(f.get('*Film Title (Original Language)*')),
        'year': f.get('CIFF Year'),
        'type': f.get('Film Type'),
        'sections': f.get('Competition / Section', []),
        'tags': f.get('Project Tags', []),
        'highlight': bool(f.get('Monthly Highlight')),
        'directors': [x for x in r['filmmakers'] if x.strip()]
                     or split(f.get('*Credit Line: Director*'), DIRECTOR_SPLIT),
        'director_credit': ws(f.get('*Credit Line: Director*')),
        'producers': ws(f.get('*Credit Line: Producer(s)*')),
        'editors': r['editors'] or split(f.get('Credit Line: Editor(s)'), EDITOR_SPLIT),
        'editor_credit': ws(f.get('Credit Line: Editor(s)')),
        'countries': list(dict.fromkeys(COUNTRY_ALIAS.get(c, c) for c in r['countries'])),
        'languages': languages,
        'runtime': round(trt / 60) if trt else None,
        'synopsis': ws(f.get('Short Synopsis')),
        'website': website(f.get('Website')),
        'streaming': [{'url': u, 'platform': PLATFORMS.get(domain(u), 'Other')}
                      for u in r['streaming_links']],
        'pni': f.get('PNI website link'),
        'still': r['still_image'] or '',
    }


def merge_artist_program_stubs(films):
    """Fold a year-less 'Artist Programs Alum' stub into the CIFF record with the same slug,
    but only when that slug has exactly one CIFF record and a director surname matches.
    Different films can share a title ("The Ark", "America"), so be conservative."""
    def surnames(f):
        return {d.split()[-1].lower() for d in f['directors'] if d.split()}
    by_slug = collections.defaultdict(list)
    for f in films:
        by_slug[f['slug']].append(f)
    drop = set()
    for slug, group in by_slug.items():
        ciff = [f for f in group if 'CIFF Alum' in f['tags']]
        stubs = [f for f in group if f['year'] is None and f['tags'] == ['Artist Programs Alum']]
        if len(ciff) != 1:
            continue
        keep = ciff[0]
        for stub in stubs:
            if surnames(stub) & surnames(keep):
                keep['tags'].append('Artist Programs Alum')
                keep['directors'] += [d for d in stub['directors'] if d not in keep['directors']]
                drop.add(stub['id'])
                print(f'merged artist-program stub: {slug}', file=sys.stderr)
    return [f for f in films if f['id'] not in drop]


def update_html(data_json, years):
    path = ROOT / 'index.html'
    html = path.read_text(encoding='utf-8')
    active = re.compile(r'^<script id="films-data" type="application/json">.*?</script>$', re.M | re.S)
    blocks = [m for m in active.finditer(html)
              if html.rfind('<!--', 0, m.start()) <= html.rfind('-->', 0, m.start())]
    if len(blocks) != 1:
        sys.exit(f'expected exactly one active films-data block in index.html, found {len(blocks)}')
    m = blocks[0]
    today = datetime.date.today().isoformat()
    replacement = ('<!-- Previous catalog data, kept for reference (superseded ' + today + ').\n'
                   + m.group(0) + '\n-->\n'
                   + f'<!-- Catalog data refreshed {today} from films_archive.json '
                   + f'({years[0]}–{years[-1]} editions) -->\n'
                   + '<script id="films-data" type="application/json">' + data_json + '</script>')
    path.write_text(html[:m.start()] + replacement + html[m.end():], encoding='utf-8')
    print(f'updated {path.name}; check the footer edition range still reads '
          f'{years[0]}–{years[-1]}', file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('archive', nargs='?', default='films_archive.json')
    ap.add_argument('--update-html', action='store_true',
                    help='comment out the current data block in index.html and insert the new one')
    args = ap.parse_args()

    raw = json.load(open(args.archive, encoding='utf-8'))
    films = merge_artist_program_stubs([convert(r) for r in raw])
    data_json = json.dumps(films, ensure_ascii=False, separators=(',', ':'))
    if '</script' in data_json or '-->' in data_json:
        sys.exit('data contains </script or --> and would break the embedding; escape it first')

    years = sorted({f['year'] for f in films if f['year']})
    counts = collections.Counter(f['year'] for f in films)
    print(f'{len(films)} titles; per year: '
          + ', '.join(f'{y}:{counts[y]}' for y in years) + f', none:{counts[None]}', file=sys.stderr)

    if args.update_html:
        update_html(data_json, years)
    else:
        (ROOT / 'films.json').write_text(data_json, encoding='utf-8')
        print('wrote films.json', file=sys.stderr)


if __name__ == '__main__':
    main()
