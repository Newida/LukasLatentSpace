(() => {
  const root = document.documentElement;
  const cssVar = (name) => getComputedStyle(root).getPropertyValue(name).trim();
  const pc = (x) => { let c = 0; while (x) { c += x & 1; x >>= 1; } return c; };
  const bitstr = (x, n) => { let s = ''; for (let i = 0; i < n; i++) s += (x >> i) & 1; return s; };
  const NS = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const txt = (parent, x, y, s, cls, anchor) => {
    const t = el('text', { x, y, class: cls || 'lbl', 'text-anchor': anchor || 'middle' }, parent);
    t.textContent = s;
    return t;
  };
  const phaseFill = (phi) => {
    let h = (phi * 180 / Math.PI) % 360; if (h < 0) h += 360;
    return `hsl(${h.toFixed(1)} var(--phase-s) var(--phase-l))`;
  };
  const fmt = (v, d = 3) => v.toFixed(d);
  const piFrac = (v) => {
    const r = v / Math.PI;
    return `${v.toFixed(3)} (${r.toFixed(3)}π)`;
  };
  function fitCanvas(c) {
    const r = c.getBoundingClientRect();
    const d = window.devicePixelRatio || 1;
    c.width = Math.max(1, Math.round(r.width * d));
    c.height = Math.max(1, Math.round(r.height * d));
    const ctx = c.getContext('2d');
    ctx.setTransform(d, 0, 0, d, 0, 0);
    return { ctx, w: r.width, h: r.height };
  }

  /* ---------- MaxCut assignments and their values on Q_3 ---------- */
  (function buildMaxCutCube() {
    // As elsewhere in the tutorial, bit i is vertex i + 1 and strings read x_1 x_2 x_3.
    const problemSvg = document.getElementById('cutProblemSvg');
    const searchSvg = document.getElementById('cutCubeSvg');
    const edgeOptions = [
      { pair: [0, 1], input: document.getElementById('cutEdge12') },
      { pair: [1, 2], input: document.getElementById('cutEdge23') },
      { pair: [0, 2], input: document.getElementById('cutEdge13') }
    ];
    let selected = 2; // 010: the middle vertex is on side 1.
    const problemPos = [[38, 166], [120, 46], [202, 166]];
    const searchPos = (x) => [60 + 190 * (x & 1) + 95 * ((x >> 2) & 1), 250 - 135 * ((x >> 1) & 1) - 70 * ((x >> 2) & 1)];
    const side = (x, i) => (x >> i) & 1;
    const signed = (v) => v > 0 ? `+${v}` : v < 0 ? `−${-v}` : '0';
    const activate = (node, action) => {
      node.addEventListener('click', action);
      node.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); action(); }
      });
    };
    // Keep controls in the DOM when redrawing, so keyboard focus survives a bit flip.
    const problemEdges = edgeOptions.map(({ pair: [i, j] }) => {
      const [x1, y1] = problemPos[i], [x2, y2] = problemPos[j];
      const line = el('line', { x1, y1, x2, y2 }, problemSvg);
      const label = txt(problemSvg, (x1 + x2) / 2 + (i === 0 && j === 1 ? -13 : i === 1 ? 13 : 0), (y1 + y2) / 2 + (j - i === 2 ? 24 : 0), '', 'cut-edge-label');
      return { line, label };
    });
    const problemNodes = problemPos.map(([cx, cy], i) => {
      const node = el('g', { class: 'cut-node', tabindex: 0, role: 'button', 'data-vertex': i + 1 }, problemSvg);
      el('circle', { cx, cy, r: 27, class: 'cut-focus' }, node);
      const disk = el('circle', { cx, cy, r: 21 }, node);
      const label = txt(node, cx, cy + 5, String(i + 1), 'gvl');
      label.setAttribute('style', 'font-size: 15px');
      const bitLabel = txt(node, cx, cy + 42, '', 'cut-bitlabel');
      activate(node, () => { selected ^= 1 << i; render(); });
      return { node, disk, bitLabel };
    });
    const searchEdges = [];
    for (let x = 0; x < 8; x++) for (let i = 0; i < 3; i++) {
      const y = x ^ (1 << i);
      if (x < y) {
        const [x1, y1] = searchPos(x), [x2, y2] = searchPos(y);
        searchEdges.push({ x, y, line: el('line', { x1, y1, x2, y2, 'data-from': bitstr(x, 3), 'data-to': bitstr(y, 3) }, searchSvg) });
      }
    }
    const selection = el('circle', { r: 27, class: 'cut-selection' }, searchSvg);
    const searchNodes = [];
    // Lexicographic tab order, independent of the integer representation of the bits.
    const order = Array.from({ length: 8 }, (_, x) => x).sort((a, b) => bitstr(a, 3).localeCompare(bitstr(b, 3)));
    for (const x of order) {
      const [cx, cy] = searchPos(x);
      const node = el('g', { class: 'cut-node', tabindex: 0, role: 'button', 'data-assignment': bitstr(x, 3) }, searchSvg);
      el('circle', { cx, cy, r: 32, class: 'cut-focus' }, node);
      const disk = el('circle', { cx, cy, r: 21 }, node);
      const value = txt(node, cx, cy + 5, '', 'cut-score');
      txt(node, cx, cy - 34, bitstr(x, 3), 'cut-bitlabel');
      activate(node, () => { selected = x; render(); });
      searchNodes[x] = { node, disk, value };
    }
    const flipButtons = Array.from({ length: 3 }, (_, i) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'btn';
      button.appendChild(document.createTextNode(`Flip x${'₁₂₃'[i]} · vertex ${i + 1}`));
      const detail = document.createElement('span'); button.appendChild(detail);
      button.addEventListener('click', () => { selected ^= 1 << i; render(); });
      document.getElementById('cutFlips').appendChild(button);
      return { button, detail };
    });
    function render() {
      const active = edgeOptions.filter(({ input }) => input.checked).map(({ pair }) => pair);
      const costs = Array.from({ length: 8 }, (_, x) => active.reduce((sum, [i, j]) => sum + (side(x, i) !== side(x, j) ? 1 : 0), 0));
      const maximum = Math.max(...costs);
      const optimal = order.filter((x) => costs[x] === maximum);
      edgeOptions.forEach(({ pair: [i, j], input }, k) => {
        const cut = side(selected, i) !== side(selected, j);
        const { line, label } = problemEdges[k];
        line.setAttribute('visibility', input.checked ? 'visible' : 'hidden');
        line.setAttribute('class', 'gedge cut-graph-edge' + (cut ? ' cut' : ''));
        label.textContent = input.checked ? (cut ? '1' : '0') : '';
      });
      problemNodes.forEach(({ node, disk, bitLabel }, i) => {
        const bit = side(selected, i);
        disk.setAttribute('class', bit ? 'gv1' : 'gv0');
        bitLabel.textContent = `x${'₁₂₃'[i]} = ${bit}`;
        node.setAttribute('aria-label', `Vertex ${i + 1}, side ${bit}. Flip bit ${i + 1}.`);
      });
      searchEdges.forEach(({ x, y, line }) => line.setAttribute('class', 'edge' + (x === selected || y === selected ? ' cut-neighbor-edge' : '')));
      const [cx, cy] = searchPos(selected);
      selection.setAttribute('cx', cx); selection.setAttribute('cy', cy);
      searchNodes.forEach(({ node, disk, value }, x) => {
        disk.setAttribute('class', `cut-disk cut-value-${costs[x]}`);
        value.setAttribute('class', `cut-score cut-score-${costs[x]}`);
        value.textContent = costs[x];
        node.setAttribute('aria-label', `Assignment ${bitstr(x, 3)}, cut size ${costs[x]}${costs[x] === maximum ? ', maximum cut' : ''}`);
        node.setAttribute('aria-pressed', String(x === selected));
      });
      const bits = bitstr(selected, 3);
      document.getElementById('cutSelected').textContent = `x = ${bits} → C(x) = ${costs[selected]} of ${active.length} edges cut`;
      const partition = (bit) => {
        const vertices = [0, 1, 2].filter((i) => side(selected, i) === bit).map((i) => i + 1);
        return vertices.length ? `{${vertices.join(', ')}}` : '∅';
      };
      document.getElementById('cutPartitions').textContent = `Side 0: ${partition(0)} · Side 1: ${partition(1)}`;
      const terms = active.map(([i, j]) => `[${side(selected, i)} ≠ ${side(selected, j)}]`);
      const values = active.map(([i, j]) => side(selected, i) !== side(selected, j) ? 1 : 0);
      document.getElementById('cutEquation').textContent = active.length
        ? `C(${bits}) = ${terms.join(' + ')} = ${values.join(' + ')} = ${costs[selected]}`
        : `C(${bits}) = 0 (there are no problem edges)`;
      document.getElementById('cutOptima').textContent = optimal.length === 8
        ? 'Maximum cut: 0. All eight assignments are optimal.'
        : `Maximum cut: ${maximum}. Attained at ${optimal.map((x) => bitstr(x, 3)).join(', ')}.`;
      flipButtons.forEach(({ button, detail }, i) => {
        const neighbor = selected ^ (1 << i);
        detail.textContent = `→ ${bitstr(neighbor, 3)} · C = ${costs[neighbor]} · ΔC = ${signed(costs[neighbor] - costs[selected])}`;
        button.setAttribute('aria-label', `Flip bit ${i + 1}: assignment ${bitstr(neighbor, 3)}, cut size ${costs[neighbor]}, change ${signed(costs[neighbor] - costs[selected])}`);
      });
    }
    edgeOptions.forEach(({ input }) => input.addEventListener('change', render));
    document.getElementById('cutComplement').addEventListener('click', () => { selected ^= 7; render(); });
    document.getElementById('cutReset').addEventListener('click', () => {
      selected = 2; edgeOptions.forEach(({ input }, k) => { input.checked = k < 2; }); render();
    });
    render();
    document.getElementById('maxcut-cube').hidden = false;
    document.getElementById('cutFallback').hidden = true;
  })();

  /* ---------- hero: 16x16 Walsh matrix ---------- */
  const walsh16 = document.getElementById('walsh16');
  function drawWalsh16() {
    const { ctx, w } = fitCanvas(walsh16);
    const n = 4, N = 16;
    const rows = [...Array(N).keys()].sort((a, b) => pc(a) - pc(b) || a - b);
    const gap = Math.max(1, w / 200), cell = (w - gap * (N - 1)) / N;
    const pos = cssVar('--pos'), neg = cssVar('--neg');
    ctx.clearRect(0, 0, w, w);
    rows.forEach((s, r) => {
      for (let x = 0; x < N; x++) {
        ctx.fillStyle = pc(s & x) % 2 ? neg : pos;
        ctx.fillRect(x * (cell + gap), r * (cell + gap), cell, cell);
      }
    });
  }

  /* ---------- the second stage: Haar wavelets on the tree ---------- */
  // Strings are integers with x_1 in bit 0. On the tree x_1 is decided at the root, so the leaf at
  // position k from the left is the string whose bits are the bits of k read backwards.
  const reverseBits = (k, n) => { let x = 0; for (let i = 0; i < n; i++) x |= ((k >> (n - 1 - i)) & 1) << i; return x; };
  // A wavelet is a branching point: its level m and the prefix p = x_1 ... x_{m-1} leading to it.
  // It is +1 below the 0-branch, -1 below the 1-branch and 0 elsewhere. Level 0 is the constant.
  const waveAt = ([m, p], x) => {
    if (m === 0) return 1;
    if ((x & ((1 << (m - 1)) - 1)) !== p) return 0;
    return (x >> (m - 1)) & 1 ? -1 : 1;
  };
  const waveletsOf = (n) => {
    const w = [[0, 0]];
    for (let m = 1; m <= n; m++) for (let k = 0; k < 1 << (m - 1); k++) w.push([m, reverseBits(k, m - 1)]);
    return w;
  };
  const haar16 = document.getElementById('haar16');
  function drawHaar16() {
    if (!haar16) return;
    const { ctx, w } = fitCanvas(haar16);
    const n = 4, N = 16;
    const gap = Math.max(1, w / 200), cell = (w - gap * (N - 1)) / N;
    const pos = cssVar('--pos'), neg = cssVar('--neg'), zero = cssVar('--code-bg');
    ctx.clearRect(0, 0, w, w);
    waveletsOf(n).forEach((wave, r) => {
      for (let k = 0; k < N; k++) {
        const v = waveAt(wave, reverseBits(k, n));
        ctx.fillStyle = v > 0 ? pos : v < 0 ? neg : zero;
        ctx.fillRect(k * (cell + gap), r * (cell + gap), cell, cell);
      }
    });
  }

  /* ---------- part 2: 8x8 Walsh grid ---------- */
  (function buildWalsh8() {
    const g = document.getElementById('walsh8');
    if (!g) return;
    const n = 3, N = 8;
    const add = (cls, text) => { const d = document.createElement('div'); d.className = cls; if (text !== undefined) d.textContent = text; g.appendChild(d); return d; };
    add('hd', 's \\ x');
    for (let x = 0; x < N; x++) add('hd', bitstr(x, n));
    add('hd', 'n−2|s|');
    let last = -1;
    [...Array(N).keys()].sort((a, b) => pc(a) - pc(b) || a - b).forEach((s) => {
      if (last !== -1 && pc(s) !== last) add('grp');
      last = pc(s);
      add('rl', bitstr(s, n));
      for (let x = 0; x < N; x++) add('t ' + (pc(s & x) % 2 ? 'n' : 'p'));
      add('ev', (n - 2 * pc(s) > 0 ? '+' : '') + (n - 2 * pc(s)));
    });
  })();

  /* ---------- part 4: diffusion lab on the cube and on the tree ---------- */
  const A = { n: 3, stage: 'cube', mode: 'classical', u: 0.25, start: 0, playing: false };
  const cubeSvg = document.getElementById('cubeSvg');
  const modeSvg = document.getElementById('modeSvg');
  const cubeTime = document.getElementById('cubeTime');
  const cubePos = (x) => {
    const b0 = x & 1, b1 = (x >> 1) & 1, b2 = (x >> 2) & 1;
    return [70 + 190 * b0 + 85 * b2, 240 - 150 * b1 - 70 * b2];
  };
  const modeOrder = [0, 1, 2, 4, 3, 5, 6, 7];
  const modeX = (s) => {
    const w = pc(s);
    const groups = [[0], [1, 2, 4], [3, 5, 6], [7]];
    const idx = groups[w].indexOf(s);
    const starts = [22, 86, 230, 374];
    return starts[w] + idx * 46 + 17;
  };
  function cubeState() {
    const { n, mode, u, start } = A;
    const P = new Array(8).fill(0), phase = new Array(8).fill(0), coef = new Array(8).fill(0), cphase = new Array(8).fill(0);
    let flip;
    if (mode === 'classical') {
      const t = 1.5 * u;
      flip = (1 - Math.exp(-2 * t)) / 2;
      for (let x = 0; x < 8; x++) { const k = pc(x ^ start); P[x] = flip ** k * (1 - flip) ** (n - k); }
      for (let s = 0; s < 8; s++) coef[s] = (pc(s & start) % 2 ? -1 : 1) * Math.exp(-2 * pc(s) * t);
      return { P, coef, flip, param: t };
    }
    const b = (Math.PI / 2) * u, c = Math.cos(b), sn = Math.sin(b);
    flip = sn * sn;
    for (let x = 0; x < 8; x++) {
      const k = pc(x ^ start);
      const mag = c ** (n - k) * sn ** k;
      P[x] = mag * mag;
      phase[x] = -k * Math.PI / 2;
    }
    for (let s = 0; s < 8; s++) cphase[s] = -b * (n - 2 * pc(s)) + (pc(s & start) % 2 ? Math.PI : 0);
    return { P, phase, cphase, flip, param: b };
  }
  // The tree: tree distance is n minus the length of the common prefix x_1 x_2 ...
  const treeDist = (x, y, n) => { for (let i = 0; i < n; i++) if (((x ^ y) >> i) & 1) return n - i; return 0; };
  const treeWaves = waveletsOf(3);
  const treeWaveX = [39, 103, 167, 213, 271, 317, 363, 409];
  const leafX = (k) => 42.5 + 45 * k;
  function treeState() {
    const { n, mode, u, start } = A;
    const P = new Array(8).fill(0), phase = new Array(8).fill(0);
    const at = treeWaves.map((w) => waveAt(w, start));
    if (mode === 'classical') {
      const t = 1.5 * u;
      // J is the highest clock that rang, P(J <= k) = exp(-2 (n - k) t); then the last J bits are uniform.
      const PJ = [Math.exp(-2 * n * t)];
      for (let k = 1; k <= n; k++) PJ.push(Math.exp(-2 * (n - k) * t) - Math.exp(-2 * (n - k + 1) * t));
      for (let x = 0; x < 8; x++) for (let k = treeDist(start, x, n); k <= n; k++) P[x] += PJ[k] / (1 << k);
      return { P, coef: at.map((v, i) => v * Math.exp(-2 * treeWaves[i][0] * t)), param: t };
    }
    const b = (Math.PI / 2) * u;
    // exp(-i b B_T) = e^{i n b} I + sum_k (-2 i sin b) e^{i b (n - 2k + 1)} A_k, where A_k spreads 2^-k over a block.
    for (let x = 0; x < 8; x++) {
      const d = treeDist(start, x, n);
      let re = d === 0 ? Math.cos(n * b) : 0, im = d === 0 ? Math.sin(n * b) : 0;
      for (let k = Math.max(d, 1); k <= n; k++) {
        const ang = b * (n - 2 * k + 1), w = -2 * Math.sin(b) / (1 << k);
        re -= w * Math.sin(ang); im += w * Math.cos(ang);
      }
      P[x] = re * re + im * im;
      phase[x] = Math.atan2(im, re);
    }
    const cphase = treeWaves.map(([m], i) => -b * (n - 2 * m) + (at[i] < 0 ? Math.PI : 0));
    return { P, phase, at, cphase, param: b };
  }
  function drawCubePanels(st, q) {
    cubeSvg.textContent = '';
    for (let x = 0; x < 8; x++) for (let i = 0; i < 3; i++) {
      const y = x ^ (1 << i);
      if (y > x) { const [x1, y1] = cubePos(x), [x2, y2] = cubePos(y); el('line', { x1, y1, x2, y2, class: 'edge' }, cubeSvg); }
    }
    for (let x = 0; x < 8; x++) {
      const [cx, cy] = cubePos(x);
      const r = 5 + 26 * Math.sqrt(st.P[x]);
      if (x === A.start) el('circle', { cx, cy, r: r + 5, class: 'startring' }, cubeSvg);
      const c = el('circle', { cx, cy, r, class: 'vtx', tabindex: 0, role: 'button', 'aria-label': `Start at ${bitstr(x, 3)}` }, cubeSvg);
      c.style.fill = q && st.P[x] > 1e-12 ? phaseFill(st.phase[x]) : 'var(--pos)';
      c.addEventListener('click', () => { A.start = x; renderA(); });
      c.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); A.start = x; renderA(); } });
      const above = cy < 150;
      txt(cubeSvg, cx, above ? cy - r - 8 : cy + r + 15, bitstr(x, 3), 'lbl-ink');
      txt(cubeSvg, cx + (x & 1 ? 1 : -1) * (r + 6), cy + 4, st.P[x].toFixed(3), 'lbl', x & 1 ? 'start' : 'end');
    }
    // mode panel
    modeSvg.textContent = '';
    const base = 108;
    ['|s| = 0', '|s| = 1', '|s| = 2', '|s| = 3'].forEach((label, w) => {
      const xs = [39, 149, 293, 391][w];
      txt(modeSvg, xs, 16, label, 'lbl-ink');
      txt(modeSvg, xs, 32, `λ = ${3 - 2 * w > 0 ? '+' : ''}${3 - 2 * w}`, 'lbl');
    });
    if (!q) el('line', { x1: 8, x2: 422, y1: base, y2: base, class: 'base' }, modeSvg);
    modeOrder.forEach((s) => {
      const cx = modeX(s);
      if (!q) {
        const v = st.coef[s], h = 58 * Math.abs(v);
        el('rect', { x: cx - 13, y: v >= 0 ? base - h : base, width: 26, height: Math.max(h, 0.5), class: v >= 0 ? 'bar-p' : 'bar-n' }, modeSvg);
      } else {
        const R = 18, ph = st.cphase[s];
        el('circle', { cx, cy: base, r: R, class: 'dial' }, modeSvg);
        const x2 = cx + R * Math.cos(ph), y2 = base - R * Math.sin(ph);
        const ln = el('line', { x1: cx, y1: base, x2, y2, 'stroke-width': 2.6, 'stroke-linecap': 'round' }, modeSvg);
        ln.style.stroke = phaseFill(ph);
        const dot = el('circle', { cx: x2, cy: y2, r: 3.2 }, modeSvg);
        dot.style.fill = phaseFill(ph);
      }
      txt(modeSvg, cx, 186, bitstr(s, 3), 'lbl');
    });
  }
  function drawTreePanels(st, q) {
    cubeSvg.textContent = '';
    const ys = [34, 88, 142, 196], l1 = [110, 290], l2 = [65, 155, 245, 335];
    l1.forEach((x) => el('line', { x1: 200, y1: ys[0], x2: x, y2: ys[1], class: 'edge' }, cubeSvg));
    l2.forEach((x, i) => el('line', { x1: l1[i >> 1], y1: ys[1], x2: x, y2: ys[2], class: 'edge' }, cubeSvg));
    for (let k = 0; k < 8; k++) el('line', { x1: l2[k >> 1], y1: ys[2], x2: leafX(k), y2: ys[3], class: 'edge' }, cubeSvg);
    [[200, ys[0]], ...l1.map((x) => [x, ys[1]]), ...l2.map((x) => [x, ys[2]])].forEach(([cx, cy]) => el('circle', { cx, cy, r: 3.5, class: 'tnode' }, cubeSvg));
    ['x₁', 'x₂', 'x₃'].forEach((s, i) => txt(cubeSvg, 4, (ys[i] + ys[i + 1]) / 2 + 4, s, 'lbl', 'start'));
    // leaves from left to right, so that Tab walks along the tree
    for (let k = 0; k < 8; k++) {
      const x = reverseBits(k, 3), cx = leafX(k), cy = ys[3];
      const r = 4 + 17 * Math.sqrt(st.P[x]);
      if (x === A.start) el('circle', { cx, cy, r: r + 4, class: 'startring' }, cubeSvg);
      const c = el('circle', { cx, cy, r, class: 'vtx', tabindex: 0, role: 'button', 'aria-label': `Start at ${bitstr(x, 3)}` }, cubeSvg);
      c.style.fill = q && st.P[x] > 1e-12 ? phaseFill(st.phase[x]) : 'var(--pos)';
      c.addEventListener('click', () => { A.start = x; renderA(); });
      c.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); A.start = x; renderA(); } });
      txt(cubeSvg, cx, 240, bitstr(x, 3), 'lbl-ink');
      txt(cubeSvg, cx, 257, st.P[x].toFixed(3), 'lbl');
    }
    // mode panel: the eight Haar wavelets, grouped by level; the speeds n - 2m match the cube's n - 2|s|
    modeSvg.textContent = '';
    const base = 108;
    [['level 0', 39], ['level 1', 103], ['level 2', 190], ['level 3', 340]].forEach(([label, xs], m) => {
      txt(modeSvg, xs, 16, label, 'lbl-ink');
      txt(modeSvg, xs, 32, `λ = ${3 - 2 * m > 0 ? '+' : ''}${3 - 2 * m}`, 'lbl');
    });
    if (!q) el('line', { x1: 8, x2: 422, y1: base, y2: base, class: 'base' }, modeSvg);
    treeWaves.forEach(([m, p], i) => {
      const cx = treeWaveX[i];
      if (!q) {
        const v = st.coef[i], h = 58 * Math.abs(v);
        el('rect', { x: cx - 13, y: v >= 0 ? base - h : base, width: 26, height: Math.max(h, 0.5), class: v >= 0 ? 'bar-p' : 'bar-n' }, modeSvg);
      } else {
        const R = 18;
        el('circle', { cx, cy: base, r: R, class: 'dial' }, modeSvg);
        if (st.at[i] !== 0) {
          const ph = st.cphase[i], x2 = cx + R * Math.cos(ph), y2 = base - R * Math.sin(ph);
          const ln = el('line', { x1: cx, y1: base, x2, y2, 'stroke-width': 2.6, 'stroke-linecap': 'round' }, modeSvg);
          ln.style.stroke = phaseFill(ph);
          const dot = el('circle', { cx: x2, cy: y2, r: 3.2 }, modeSvg);
          dot.style.fill = phaseFill(ph);
        }
      }
      txt(modeSvg, cx, 186, m === 0 ? 'const' : m === 1 ? 'root' : bitstr(p, m - 1), 'lbl');
    });
  }
  const LAB_TEXT = {
    cube: {
      pos: 'Positions: corners', modes: 'Frequencies: Walsh modes',
      posAria: 'Three-dimensional Hamming cube with probabilities on its corners', modesAria: 'Walsh mode coefficients of the current state',
      k: ['Per-bit flip probability', 'P(start corner)', 'P(opposite corner)'],
      quantum: ['Each dial is one Walsh mode of the amplitude. Its length never changes; it rotates at speed n − 2|s|, so modes of different weight drift out of step.',
        'Circle area is probability; colour is the phase of the amplitude. Corners at the same distance from the start share a phase, (−i)^k.'],
      classical: ['Each bar is one Walsh coefficient of the distribution, relative to the constant mode. It decays as e^(−2|s|t); a negative bar means the mode flips sign at the start corner.',
        'Circle area is probability. The dashed ring marks the start corner.'],
    },
    tree: {
      pos: 'Positions: leaves', modes: 'Frequencies: Haar wavelets',
      posAria: 'Binary tree with three levels and probabilities on its eight leaves', modesAria: 'Haar wavelet coefficients of the current state',
      k: ['P(start leaf)', 'P(sibling)', 'P(other half)'],
      quantum: ['Each dial is one Haar wavelet of the amplitude. It rotates at speed n − 2m with its level m, the same speeds as on the cube. Empty dials are wavelets that do not touch the start leaf.',
        'Circle area is probability; colour is the phase of the amplitude. The other half of the tree never gets more than 1/4 in total.'],
      classical: ['Each bar is one Haar wavelet times its value at the start leaf (+1, −1 or 0). It decays as e^(−2mt) with its level m. Only one wavelet per level touches the start leaf.',
        'Circle area is probability. The dashed ring marks the start leaf.'],
    },
  };
  function drawLab() {
    const tree = A.stage === 'tree', q = A.mode === 'quantum';
    const st = tree ? treeState() : cubeState();
    if (tree) drawTreePanels(st, q); else drawCubePanels(st, q);
    const T = LAB_TEXT[A.stage];
    document.getElementById('posLabel').textContent = T.pos;
    document.getElementById('modeLabel').textContent = T.modes;
    cubeSvg.setAttribute('aria-label', T.posAria);
    modeSvg.setAttribute('aria-label', T.modesAria);
    T.k.forEach((s, i) => { document.getElementById(`roK${i + 1}`).textContent = s; });
    document.getElementById('cubeTimeLabel').textContent = q ? 'β' : 't';
    document.getElementById('cubeTimeOut').textContent = q ? `${st.param.toFixed(3)} (${(st.param / Math.PI).toFixed(3)}π)` : st.param.toFixed(3);
    let ro;
    if (tree) {
      let far = 0;
      for (let x = 0; x < 8; x++) if (treeDist(A.start, x, 3) === 3) far += st.P[x];
      ro = [st.P[A.start], st.P[A.start ^ 4], far];
    } else {
      ro = [st.flip, st.P[A.start], st.P[A.start ^ 7]];
    }
    ['roFlip', 'roStart', 'roOpp'].forEach((id, i) => { document.getElementById(id).textContent = ro[i].toFixed(3); });
    const [modeCap, colorNote] = q ? T.quantum : T.classical;
    document.getElementById('modeCaption').textContent = modeCap;
    document.getElementById('cubeColorNote').textContent = colorNote;
  }
  function renderA() { A.u = cubeTime.value / 1000; drawLab(); }
  cubeTime.addEventListener('input', renderA);
  const setMode = (m) => {
    A.mode = m;
    document.getElementById('modeC').setAttribute('aria-pressed', m === 'classical');
    document.getElementById('modeQ').setAttribute('aria-pressed', m === 'quantum');
    renderA();
  };
  document.getElementById('modeC').addEventListener('click', () => setMode('classical'));
  document.getElementById('modeQ').addEventListener('click', () => setMode('quantum'));
  const setStage = (s) => {
    A.stage = s;
    document.getElementById('stageCube').setAttribute('aria-pressed', s === 'cube');
    document.getElementById('stageTree').setAttribute('aria-pressed', s === 'tree');
    renderA();
  };
  document.getElementById('stageCube').addEventListener('click', () => setStage('cube'));
  document.getElementById('stageTree').addEventListener('click', () => setStage('tree'));
  const playBtn = document.getElementById('cubePlay');
  let rafId = null, lastT = 0;
  const step = (ts) => {
    if (!A.playing) return;
    const dt = lastT ? (ts - lastT) / 1000 : 0; lastT = ts;
    let v = +cubeTime.value + dt * 220;
    if (v >= 1000) { v = 1000; A.playing = false; playBtn.textContent = 'Play'; }
    cubeTime.value = v; renderA();
    if (A.playing) rafId = requestAnimationFrame(step);
  };
  playBtn.addEventListener('click', () => {
    if (A.playing) { A.playing = false; playBtn.textContent = 'Play'; cancelAnimationFrame(rafId); return; }
    if (+cubeTime.value >= 1000) cubeTime.value = 0;
    A.playing = true; lastT = 0; playBtn.textContent = 'Pause';
    rafId = requestAnimationFrame(step);
  });

  /* ---------- part 7: QAOA depth 1 on the prism, with the cube or the tree as the stage ---------- */
  const n = 6, N = 1 << n;
  const edges = [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [0, 3], [1, 4], [2, 5]];
  // W[s] = |s| is the cube level of the Walsh mode s; BL[s], the position of the last 1 in s, is its tree level.
  const C = new Float64Array(N), W = new Int32Array(N), BL = new Int32Array(N);
  for (let x = 0; x < N; x++) {
    W[x] = pc(x);
    BL[x] = x ? 32 - Math.clz32(x) : 0;
    for (const [i, j] of edges) if (((x >> i) & 1) !== ((x >> j) & 1)) C[x]++;
  }
  let Cmax = 0; for (let x = 0; x < N; x++) Cmax = Math.max(Cmax, C[x]);
  const uniformHist = new Float64Array(Cmax + 1);
  for (let x = 0; x < N; x++) uniformHist[C[x]] += 1 / N;

  function fwht(a) {
    for (let h = 1; h < a.length; h <<= 1)
      for (let i = 0; i < a.length; i += h << 1)
        for (let j = i; j < i + h; j++) { const u = a[j], v = a[j + h]; a[j] = u + v; a[j + h] = u - v; }
  }
  const re = new Float64Array(N), im = new Float64Array(N);
  // One QAOA layer as a split-step Fourier step: cost phase, WHT, mixer phase, WHT back.
  // The Walsh modes diagonalize both stages; mode s rotates with n - 2 level[s], where level is |s| or the tree level.
  function simulate(g, b, detail, level) {
    const a0 = 1 / Math.sqrt(N);
    for (let x = 0; x < N; x++) { const ang = -g * C[x]; re[x] = a0 * Math.cos(ang); im[x] = a0 * Math.sin(ang); }
    fwht(re); fwht(im);
    let spec = null;
    if (detail) { spec = new Float64Array(n + 1); for (let s = 0; s < N; s++) spec[level[s]] += (re[s] * re[s] + im[s] * im[s]) / N; }
    for (let s = 0; s < N; s++) {
      const ang = -b * (n - 2 * level[s]), c = Math.cos(ang), sn = Math.sin(ang);
      const r = re[s], i = im[s];
      re[s] = r * c - i * sn; im[s] = r * sn + i * c;
    }
    fwht(re); fwht(im);
    let E = 0;
    const P = detail ? new Float64Array(N) : null;
    for (let x = 0; x < N; x++) {
      const p = (re[x] * re[x] + im[x] * im[x]) / (N * N);
      E += p * C[x];
      if (P) P[x] = p;
    }
    return detail ? { E, P, spec } : E;
  }

  const GX = 120, GY = 80, GMAX = Math.PI;
  // On the tree the mixer phases repeat only after beta = pi, on the cube already after pi/2.
  const LAND = {
    cube: { level: W, bmax: Math.PI / 2, ticks: ['0', 'π/8', 'π/4', '3π/8', 'π/2'], spec: 'Walsh weight by |s|',
      specAria: 'Fourier weight of the state grouped by Hamming weight of the frequency' },
    tree: { level: BL, bmax: Math.PI, ticks: ['0', 'π/4', 'π/2', '3π/4', 'π'], spec: 'Weight by tree level',
      specAria: 'Weight of the state on each level of the tree' },
  };
  for (const L of Object.values(LAND)) {
    const grid = new Float64Array(GX * GY);
    let gmin = Infinity, gmaxv = -Infinity, best = { g: 0, b: 0, E: -Infinity };
    for (let j = 0; j < GY; j++) for (let i = 0; i < GX; i++) {
      const g = (i + 0.5) / GX * GMAX, b = (j + 0.5) / GY * L.bmax;
      const E = simulate(g, b, false, L.level);
      grid[j * GX + i] = E;
      if (E < gmin) gmin = E;
      if (E > gmaxv) gmaxv = E;
    }
    // refine the best point on a finer local grid
    let bi = 0; for (let k = 1; k < grid.length; k++) if (grid[k] > grid[bi]) bi = k;
    const g0 = ((bi % GX) + 0.5) / GX * GMAX, b0 = (Math.floor(bi / GX) + 0.5) / GY * L.bmax;
    for (let a = -20; a <= 20; a++) for (let c = -20; c <= 20; c++) {
      const g = g0 + a * GMAX / GX / 20, b = b0 + c * L.bmax / GY / 20;
      if (g < 0 || g > GMAX || b < 0 || b > L.bmax) continue;
      const E = simulate(g, b, false, L.level);
      if (E > best.E) best = { g, b, E };
    }
    Object.assign(L, { grid, gmin, gmaxv, best });
  }
  let land = LAND.cube;

  const B = { g: land.best.g, b: land.best.b };
  const heat = document.getElementById('heat');
  const gS = document.getElementById('gSlider'), bS = document.getElementById('bSlider');
  const PAD = { l: 50, r: 12, t: 10, b: 40 };
  const hex = (c) => { c = c.replace('#', ''); return [0, 2, 4].map((k) => parseInt(c.slice(k, k + 2), 16)); };
  function ramp(t, lo, mid, hi) {
    const [a, b2, u] = t < 0.5 ? [lo, mid, t * 2] : [mid, hi, (t - 0.5) * 2];
    return `rgb(${a.map((v, k) => Math.round(v + (b2[k] - v) * u)).join(',')})`;
  }
  function drawHeat() {
    const { ctx, w, h } = fitCanvas(heat);
    const lo = hex(cssVar('--heat-lo')), mid = hex(cssVar('--heat-mid')), hi = hex(cssVar('--heat-hi'));
    const ink = cssVar('--ink'), muted = cssVar('--muted'), rule = cssVar('--rule'), panel = cssVar('--panel');
    const pw = w - PAD.l - PAD.r, ph = h - PAD.t - PAD.b;
    const { grid, gmin, gmaxv, bmax, ticks } = land;
    ctx.clearRect(0, 0, w, h);
    const cw = pw / GX, ch = ph / GY;
    for (let j = 0; j < GY; j++) for (let i = 0; i < GX; i++) {
      const t = (grid[j * GX + i] - gmin) / (gmaxv - gmin);
      ctx.fillStyle = ramp(t, lo, mid, hi);
      ctx.fillRect(PAD.l + i * cw, PAD.t + (GY - 1 - j) * ch, cw + 0.6, ch + 0.6);
    }
    ctx.strokeStyle = rule; ctx.lineWidth = 1;
    ctx.strokeRect(PAD.l + 0.5, PAD.t + 0.5, pw - 1, ph - 1);
    ctx.fillStyle = muted;
    ctx.font = `11px ${cssVar('--f-mono')}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ['0', 'π/4', 'π/2', '3π/4', 'π'].forEach((lab, k) => {
      const x = PAD.l + pw * k / 4;
      ctx.fillText(lab, x, PAD.t + ph + 6);
    });
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ticks.forEach((lab, k) => {
      const y = PAD.t + ph - ph * k / 4;
      ctx.fillText(lab, PAD.l - 6, y);
    });
    ctx.fillStyle = ink;
    ctx.font = `italic 14px ${cssVar('--f-math')}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.fillText('γ', PAD.l + pw / 2, h - 4);
    ctx.save(); ctx.translate(13, PAD.t + ph / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('β', 0, 4); ctx.restore();
    // marker
    const mx = PAD.l + B.g / GMAX * pw, my = PAD.t + ph - B.b / bmax * ph;
    ctx.lineWidth = 3; ctx.strokeStyle = panel;
    ctx.beginPath(); ctx.arc(mx, my, 7, 0, 2 * Math.PI); ctx.stroke();
    ctx.lineWidth = 1.6; ctx.strokeStyle = ink;
    ctx.beginPath(); ctx.arc(mx, my, 7, 0, 2 * Math.PI); ctx.stroke();
  }
  const graphPos = [[110, 18], [192, 160], [28, 160], [110, 72], [150, 136], [70, 136]];
  function drawB() {
    const r = simulate(B.g, B.b, true, land.level);
    let mode = 0; for (let x = 1; x < N; x++) if (r.P[x] > r.P[mode]) mode = x;
    let popt = 0; for (let x = 0; x < N; x++) if (C[x] === Cmax) popt += r.P[x];
    document.getElementById('roE').textContent = r.E.toFixed(3);
    document.getElementById('roR').textContent = (r.E / Cmax).toFixed(3);
    document.getElementById('roP').textContent = popt.toFixed(3);
    document.getElementById('roMode').textContent = `${bitstr(mode, n)} (cut ${C[mode]})`;
    document.getElementById('gOut').textContent = piFrac(B.g);
    document.getElementById('bOut').textContent = piFrac(B.b);
    // graph
    const gs = document.getElementById('graphSvg'); gs.textContent = '';
    for (const [i, j] of edges) {
      const cut = ((mode >> i) & 1) !== ((mode >> j) & 1);
      el('line', { x1: graphPos[i][0], y1: graphPos[i][1], x2: graphPos[j][0], y2: graphPos[j][1], class: 'gedge' + (cut ? ' cut' : '') }, gs);
    }
    graphPos.forEach(([x, y], i) => {
      el('circle', { cx: x, cy: y, r: 12, class: (mode >> i) & 1 ? 'gv1' : 'gv0' }, gs);
      txt(gs, x, y + 4, String(i + 1), 'gvl');
    });
    // histogram
    const hs = document.getElementById('histSvg'); hs.textContent = '';
    const hist = new Float64Array(Cmax + 1); for (let x = 0; x < N; x++) hist[C[x]] += r.P[x];
    let top = 0; for (let c = 0; c <= Cmax; c++) top = Math.max(top, hist[c], uniformHist[c]);
    top = Math.max(0.05, top);
    const x0 = 14, bw = (210 - x0) / (Cmax + 1), base = 140;
    el('line', { x1: x0 - 4, x2: 214, y1: base, y2: base, class: 'base' }, hs);
    for (let c = 0; c <= Cmax; c++) {
      const hh = 120 * hist[c] / top, hu = 120 * uniformHist[c] / top;
      el('rect', { x: x0 + c * bw + 3, y: base - hh, width: bw - 6, height: Math.max(hh, 0.5), class: c === Cmax ? 'bar-n' : 'bar-p' }, hs);
      if (hu > 0) el('rect', { x: x0 + c * bw + 1.5, y: base - hu, width: bw - 3, height: hu, class: 'ref' }, hs);
      txt(hs, x0 + c * bw + bw / 2, base + 14, String(c), 'lbl');
    }
    txt(hs, 214, 10, `max ${top.toFixed(2)}`, 'lbl', 'end');
    // spectrum, grouped by the level of the current stage
    const ss = document.getElementById('specSvg'); ss.textContent = '';
    const sw = (210 - x0) / (n + 1);
    el('line', { x1: x0 - 4, x2: 214, y1: base, y2: base, class: 'base' }, ss);
    for (let k = 0; k <= n; k++) {
      const hh = 120 * r.spec[k];
      el('rect', { x: x0 + k * sw + 3, y: base - hh, width: sw - 6, height: Math.max(hh, 0.5), class: 'bar-p' }, ss);
      txt(ss, x0 + k * sw + sw / 2, base + 14, String(k), 'lbl');
      if (r.spec[k] > 0.004) txt(ss, x0 + k * sw + sw / 2, base - hh - 4, r.spec[k].toFixed(2), 'lbl');
    }
    drawHeat();
  }
  function setB(g, b, fromSlider) {
    B.g = Math.min(GMAX, Math.max(0, g));
    B.b = Math.min(land.bmax, Math.max(0, b));
    if (!fromSlider) { gS.value = Math.round(B.g / GMAX * 1000); bS.value = Math.round(B.b / land.bmax * 1000); }
    drawB();
  }
  gS.addEventListener('input', () => setB(gS.value / 1000 * GMAX, B.b, true));
  bS.addEventListener('input', () => setB(B.g, bS.value / 1000 * land.bmax, true));
  document.getElementById('bestBtn').addEventListener('click', () => setB(land.best.g, land.best.b));
  const pick = (e) => {
    const r = heat.getBoundingClientRect();
    const pw = r.width - PAD.l - PAD.r, ph = r.height - PAD.t - PAD.b;
    const g = (e.clientX - r.left - PAD.l) / pw * GMAX;
    const b = (r.height - PAD.b - (e.clientY - r.top)) / ph * land.bmax;
    setB(g, b);
  };
  heat.addEventListener('pointerdown', (e) => { heat.setPointerCapture(e.pointerId); pick(e); });
  heat.addEventListener('pointermove', (e) => { if (e.buttons & 1) pick(e); });
  heat.addEventListener('keydown', (e) => {
    const dg = GMAX / 100, db = land.bmax / 100;
    const moves = { ArrowLeft: [-dg, 0], ArrowRight: [dg, 0], ArrowUp: [0, db], ArrowDown: [0, -db] };
    if (moves[e.key]) { e.preventDefault(); setB(B.g + moves[e.key][0], B.b + moves[e.key][1]); }
  });
  const setLand = (name) => {
    land = LAND[name];
    document.getElementById('landCube').setAttribute('aria-pressed', name === 'cube');
    document.getElementById('landTree').setAttribute('aria-pressed', name === 'tree');
    document.getElementById('specLabel').textContent = land.spec;
    document.getElementById('specSvg').setAttribute('aria-label', land.specAria);
    document.getElementById('heatMin').textContent = land.gmin.toFixed(2);
    document.getElementById('heatMax').textContent = land.gmaxv.toFixed(2);
    setB(land.best.g, land.best.b);
  };
  document.getElementById('landCube').addEventListener('click', () => setLand('cube'));
  document.getElementById('landTree').addEventListener('click', () => setLand('tree'));

  /* ---------- init and theme/resize handling ---------- */
  function redrawCanvases() { drawWalsh16(); drawHaar16(); drawHeat(); }
  renderA();
  setLand('cube');
  drawWalsh16();
  drawHaar16();
  try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', redrawCanvases); } catch (e) {}
  new MutationObserver(redrawCanvases).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(() => redrawCanvases());
    ro.observe(walsh16); ro.observe(heat);
    if (haar16) ro.observe(haar16);
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(redrawCanvases);
})();
