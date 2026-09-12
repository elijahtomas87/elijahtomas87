# Profile artwork sources

The profile uses original SVG artwork with light/dark and desktop/compact variants. The main animation is lossless WebP, with GIF fallbacks and SVG stills for reduced motion. Contribution squares preserve GitHub's daily counts and intensity levels; the glow and scanner are decorative.

## Regenerate the artwork

Install Python with the dependencies in `requirements.txt` and Node.js with the dependencies in `package.json`. Run these commands from the repository root:

```sh
python3 -m pip install -r assets/readme/source/requirements.txt
npm install --prefix assets/readme/source
python3 assets/readme/source/create_sources.py
python3 assets/readme/source/render_motion.py
python3 assets/readme/source/render_quality.py
python3 assets/readme/source/check_assets.py
```

`create_sources.py` contains the editable vector geometry, colors and labels. `motion.json` defines the 8.8-second loop, including its 2.75-second still hold. `render_quality.py` exports the desktop animation at 2400 × 1360 and the compact animation at 1080 × 1515. Both renderers check timing, loop continuity and file size; the WebP renderer also compares the settled pixels with the source render. Temporary review images are written to the ignored `assets/readme/preview/` directory.

## Refresh the contribution snapshot manually

The calendar is a dated snapshot, not a live activity feed. To refresh it from the activity GitHub currently exposes on the public profile:

```sh
python3 assets/readme/source/contributions.py --fetch-public
```

The generator reads public counts without a token. It preserves GitHub's dates and intensity levels, and rejects incomplete or missing source data. Anonymized private activity appears only when enabled in the profile's contribution settings. Generated images include the capture date and visibility scope. No refresh workflow is active.

`static.md` provides the complete profile with still images. Keep its text aligned with the root README when editing project descriptions.
