# Sources of the QAOA and GA tutorials

Run each script from its own folder. They need numpy, scipy and markdown-it-py.

| Folder | What it builds |
|---|---|
| `qaoa_lukaslatentspace_v3/` | Reference only. `post.md` and `build.py` of the first LukasLatentSpace-style version; `build.py` no longer runs because it patched a page that was since replaced. `footer.txt` and `style.css` are still used by the other builds. |
| `qaoa_slide_version/` | `build_ad.py` writes `../../slide_version/`; `engine.js` and `test_engine.js` (run with `node`) simulate the prism; `verify*.py`, `tune.py`, `more.py` produce and check the numbers in `data.json`. |
| `ga_tutorial/` | `build_ga.py` writes `../../ga/`. |
| `qaoa_geometries/` | `geo.py`: QAOA on the cube versus a ring, a complete graph and a Hamming-weight slice (results in `geo_results.json`). |
