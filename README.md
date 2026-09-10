# devoncallan.github.io

Interactive HTML explorers, hosted for collaborators at
**https://devoncallan.github.io/**

## Adding or updating a page

1. Copy the HTML file into `tools/` (any name — `tools/my-thing.html`).
2. Run `./publish` (optionally with a message: `./publish "added run 04"`).

That's it. GitHub Pages picks it up within a minute or so.

`./publish` regenerates `index.html` by reading each file in `tools/`:

| Shown on the index | Comes from |
|---|---|
| Name | the page's `<title>` |
| Description | the page's `<meta name="description">` |
| Date | last commit that touched the file |
| Size | the file on disk |

Replacing a file updates its row. Deleting a file removes it.

The order on the index is the order the files are listed in `site.json`. Move
an entry up or down there to reorder the page. Anything in `tools/` that isn't
listed in `site.json` appears after the listed pages, most recently changed
first.

### Changing a label without editing the page

Put it in `site.json` — those values win, so re-exporting a tool page never
loses its label:

```json
"tools": {
  "my-thing.html": {
    "title": "Nicer name",
    "description": "One line about what it shows.",
    "hidden": false
  }
}
```

Set `"hidden": true` to keep a page on the site but off the index — the URL
still works, so you can send it to one person without listing it.

### Rebuild without publishing

`python3 build.py` writes `index.html` and stops. Open `index.html` in a
browser to check it before pushing.

## Notes

- Every page is self-contained: one HTML file, data included, no build step.
- `robots.txt` and a `noindex` tag on every page keep the site out of search
  results. It is still a public URL — anyone with the link can read it.
- `build.py` adds a doctype and the `noindex` tag to a page in `tools/` if it
  is missing them. Nothing else in your files is touched.
