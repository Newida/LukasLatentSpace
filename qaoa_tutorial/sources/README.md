# Sources of the QAOA and GA tutorials

Run each script from its own folder. They need numpy, scipy and markdown-it-py.

| Folder | What it builds |
|---|---|
| `qaoa_lukaslatentspace_v3/` | Reference only. `post.md` and `build.py` of the first LukasLatentSpace-style version; `build.py` no longer runs because it patched a page that was since replaced. `footer.txt` and `style.css` are still used by the other builds. |
| `qaoa_slide_version/` | `build_ad.py` writes `../../slide_version/`; `engine.js` and `test_engine.js` (run with `node`) simulate the prism; `verify*.py`, `tune.py`, `more.py` produce and check the numbers in `data.json`. |
| `ga_tutorial/` | `build_ga.py` writes `../../ga/`. |
| `qaoa_geometries/` | `geo.py`: QAOA on the cube versus a ring, a complete graph and a Hamming-weight slice (results in `geo_results.json`). Superseded by `qaoa_geometry_slots/stage_table.py`, which optimises more carefully. |
| `qaoa_geometry_slots/` | The current tutorial, in which the cube is one possible "stage" and a tree runs alongside it. `build_page.py` turns `../../QAOAOnTheHammingCube` into `../../qaoa_hamming_cube.html`, using `page/style.css`, `page/page.js` and the toy blocks in `page/snippets/`. Those pieces were cut out of the hand-edited page of commit f690c1a by `extract_page_parts.py` (one-off). The numbers come from `tree_geometry.py` (tree Laplacian, wavelets, diffusion tables, depth 1 on the prism, the 720 vertex orders), `final_numbers_v2.py` (cube versus tree at depths 1 to 3; the logs of two seeds) and `stage_table.py` (the comparison table of "Swapping the stage"). `explore_problems.py` was a first look at which problems to compare and is not quoted. Use one BLAS thread (`OMP_NUM_THREADS=1`) for the parallel scripts. |
