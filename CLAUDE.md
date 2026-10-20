# CIFF Back Catalog

A single-page, searchable catalog of Camden International Film Festival / Points North
Institute films. Everything lives in `index.html`: CSS, markup, the film data (a JSON
`<script id="films-data" type="application/json">` block), and the vanilla JS that reads it.
There is no build step, framework, or package manager. Open the file, or serve it with
`python3 -m http.server`, to view it.

## Refreshing the data

The source is Points North's Airtable export. Its back catalog page is
https://pointsnorthinstitute.org/ciff/backcatalog/.

```
curl -o films_archive.json https://ciffwebsiteimages.s3.amazonaws.com/films_archive.json
python3 tools/build_data.py films_archive.json            # writes films.json to inspect
python3 tools/build_data.py films_archive.json --update-html
```

`--update-html` wraps the current active data block in an HTML comment and inserts the new
block after it. **The owner wants old data commented out, not deleted.** Before removing an
older commented block (each is about 1.3 MB), ask first.

After a refresh:
- Update the edition range in the footer (`Built from the festival's own catalog data ·
  YYYY–YYYY editions`). Comment out the old line rather than deleting it.
- The README states the year range and country count; tell the owner if they're stale
  rather than rewriting the README, which is in their voice.
- Look over what changed for existing records, not just the new years. Upstream edits
  (synopses filled in, runtimes fixed, a film's year changing) come through too.
- Check that the page renders: tally numbers, the year chart's newest bars, and a film dialog.

`films_archive.json` and `films.json` are gitignored; don't commit them.

## Cleaning rules (in tools/build_data.py)

These were reverse-engineered to match the original 2005–2024 data; keep them unless the
owner asks otherwise.
- **Runtime** comes from `TRT` (seconds) converted to minutes. Don't use `runtime_str`; it's h:mm.
- **Countries:** merge only unambiguous aliases (`COUNTRY_ALIAS`). Indigenous nations such
  as Wabanaki Territory are deliberate entries and stay as they are. Add new aliases only when
  the match is obvious, and say so in your summary.
- **Streaming platform** comes from the link's domain via `PLATFORMS`; anything else is "Other".
- **Duplicate slugs:** a year-less "Artist Programs Alum" stub is merged into the CIFF record
  only when that slug has exactly one CIFF record and a director surname matches. Several
  different films share titles ("The Ark", "America"), so don't merge more aggressively.
- Filmmaker bios and headshots are dropped; bios are empty in the source.

## Conventions

- Keep the record shape stable (`id, slug, title, year, type, sections, tags, highlight,
  directors, director_credit, producers, editors, editor_credit, countries, languages,
  runtime, synopsis, website, streaming, pni, still`). The JS in `index.html` depends on it.
- Theme colors are CSS custom properties on `:root`, with dark-mode overrides. Reuse the
  tokens rather than hard-coding colors.
- Data and stills are © Points North Institute; every film links back to its page there.
