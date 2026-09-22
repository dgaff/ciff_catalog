# CIFF Back Catalog

I wanted a more easily searchable CIFF and Points North back catalog than what's on the Points North Institute's [Back Catalog](https://pointsnorthinstitute.org/ciff/backcatalog/) webpage.

This page currently covers 2005-2024. I'm not sure why 2025 is missing, and the 2026 festival just finished. I didn't give Claude a design system, so it has the usual Claude web output. It's a future project to skin it closer to the Points North look and feel.

## Refreshing the data and a note about thumbnails

Get the films archive and put it in the data section in index.html.

```
curl -o films_archive.json https://ciffwebsiteimages.s3.amazonaws.com/films_archive.json
```

## Notes on data cleaning

- **Runtime** — source `TRT` is seconds; the site's own `runtime_str` is h:mm,
  which reads as seconds to a casual viewer. Converted to minutes.
- **Countries** — 135 raw values → 128. Merged only unambiguous aliases:
  USA→United States, UK→United Kingdom, México→Mexico, The
  Netherlands→Netherlands, Russian Federation→Russia, Republic
  Czech→Czech Republic, "Congo, Democratic Republic of"→Democratic Republic
  of Congo. Indigenous nations (Wabanaki Territory, Yurok Nation, Haida Gwaii,
  etc.) are deliberate entries in the source and were left as they are.
- **Duplicate slugs** — some are genuinely different films sharing a title
  (three unrelated films called "The Ark"; two called "America"). Only merged
  an artist-program stub into a CIFF record when that slug had exactly one
  CIFF record and the director credits were compatible — 2 merges
  (Melting Snow, North by Current).
- **Streaming platform** derived from the link's domain (Vimeo 191, Amazon 93,
  iTunes 53, YouTube 52, Kanopy 28, …).
- Filmmaker bios are empty for every record in the source; headshots exist for
  only 78. Both dropped.

## Credits

Catalog data and still images © Points North Institute / Camden International
Film Festival. Every film links back to its page on [pointsnorthinstitute.org](https://pointsnorthinstitute.org).
