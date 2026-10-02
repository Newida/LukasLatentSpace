  /* ---------- Toy 1: sliding from the cube to the cut ---------- */
  (() => {
    const byId = (id) => document.getElementById(id);
    const slider = byId('slS'), levelsSvg = byId('slLevels'), histSvg = byId('slHist');
    const last = SLIDE.s.length - 1;
    const present = [];
    for (let c = 0; c <= PRISM.Cmax; c++) if (PRISM.C.some((v) => v === c)) present.push(c);
    let timer = null;

    function drawLevels(k) {
      levelsSvg.textContent = '';
      const L = 34, R = 290, TOP = 10, B = 172, lo = -7.5, hi = 6.5;
      const X = (s) => L + (R - L) * s, Y = (e) => B - (B - TOP) * (e - lo) / (hi - lo);
      [-6, -3, 0, 3, 6].forEach((e) => { el('line', { x1: L, x2: R, y1: Y(e), y2: Y(e), class: 'grid' }, levelsSvg); txt(levelsSvg, L - 6, Y(e) + 4, String(e), 'lbl', 'end'); });
      [0, 0.5, 1].forEach((s) => txt(levelsSvg, X(s), B + 14, String(s), 'lbl'));
      txt(levelsSvg, (L + R) / 2, B + 27, 's', 'lbl');
      const level = (j, cls) => el('polyline', { points: SLIDE.s.map((s, i) => `${X(s).toFixed(1)},${Y(SLIDE.levels[i][j]).toFixed(1)}`).join(' '), class: cls }, levelsSvg);
      for (let j = SLIDE.levels[0].length - 1; j >= 2; j--) level(j, 'lvl');
      level(1, 'lvl1');
      level(0, 'lvl0');
      const s = SLIDE.s[k], e0 = SLIDE.levels[k][0], e1 = SLIDE.levels[k][1];
      el('line', { x1: X(s), x2: X(s), y1: TOP, y2: B, class: 'sline' }, levelsSvg);
      el('line', { x1: X(s), x2: X(s), y1: Y(e0), y2: Y(e1), class: 'gapbar' }, levelsSvg);
      [e0, e1].forEach((e) => el('line', { x1: X(s) - 4, x2: X(s) + 4, y1: Y(e), y2: Y(e), class: 'gapbar' }, levelsSvg));
      el('circle', { cx: X(s), cy: Y(e0), r: 3.5, class: 'dot' }, levelsSvg);
      txt(levelsSvg, X(s) + (s > 0.8 ? -7 : 7), (Y(e0) + Y(e1)) / 2 + 4, 'gap', 'lbl-ink', s > 0.8 ? 'end' : 'start');
    }

    function drawHist(k) {
      histSvg.textContent = '';
      const L = 34, R = 290, TOP = 10, B = 172, d = SLIDE.dists[k], u = SLIDE.dists[0];
      const Y = (v) => B - (B - TOP) * v, bw = (R - L) / present.length;
      [0, 0.5, 1].forEach((v) => { el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'grid' }, histSvg); txt(histSvg, L - 6, Y(v) + 4, v.toFixed(1), 'lbl', 'end'); });
      present.forEach((c, i) => {
        const x = L + i * bw, h = B - Y(d[c]);
        el('rect', { x: x + 6, y: Y(d[c]), width: bw - 12, height: Math.max(h, 0.5), class: c === PRISM.Cmax ? 'bar-n' : 'bar-p' }, histSvg);
        el('rect', { x: x + 4, y: Y(u[c]), width: bw - 8, height: B - Y(u[c]), class: 'ref' }, histSvg);
        txt(histSvg, x + bw / 2, B + 14, String(c), 'lbl');
      });
      const xm = L + (present.length - 1) * bw + bw / 2;
      txt(histSvg, xm, Math.max(Y(d[PRISM.Cmax]) - 5, TOP + 9), d[PRISM.Cmax].toFixed(2), 'lbl-ink');
      txt(histSvg, (L + R) / 2, B + 27, 'cut value', 'lbl');
    }

    function draw() {
      const k = +slider.value, st = slideStats(k);
      byId('slSOut').textContent = SLIDE.s[k].toFixed(2);
      byId('slGap').textContent = st.gap.toFixed(3);
      byId('slMin').textContent = `${MIN_GAP.gap.toFixed(3)} at s = ${MIN_GAP.s.toFixed(2)}`;
      byId('slP').textContent = st.pmax.toFixed(3);
      byId('slE').textContent = st.mean.toFixed(2);
      drawLevels(k);
      drawHist(k);
    }

    function stop() { clearInterval(timer); timer = null; byId('slPlay').textContent = 'Play'; }
    byId('slPlay').addEventListener('click', () => {
      if (timer) { stop(); return; }
      if (+slider.value >= last) slider.value = 0;
      byId('slPlay').textContent = 'Pause';
      timer = setInterval(() => {
        slider.value = Math.min(last, +slider.value + 1);
        draw();
        if (+slider.value >= last) stop();
      }, 45);
    });
    slider.addEventListener('input', () => { if (timer) stop(); draw(); });
    draw();
  })();

  /* ---------- Toy 2: walk slowly, or walk cleverly ---------- */
  (() => {
    const byId = (id) => document.getElementById(id);
    const pSlider = byId('wkP'), tSlider = byId('wkT'), anglesSvg = byId('wkAngles'), curveSvg = byId('wkCurve');
    const TMAX = 20, DT = 0.05, PER = 20;
    let fine = null, curve = null, curveP = 0, pending = false;

    function drawAngles(p, ramp_, tuned) {
      anglesSvg.textContent = '';
      const L = 34, R = 290, TOP = 10, B = 172, top = Math.PI / 2;
      const Y = (v) => B - (B - TOP) * Math.min(v, top) / top, w = (R - L) / p, bw = Math.min(16, w * 0.3);
      [0, 0.5, 1, 1.5].forEach((v) => { el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'grid' }, anglesSvg); txt(anglesSvg, L - 6, Y(v) + 4, v.toFixed(1), 'lbl', 'end'); });
      for (let k = 0; k < p; k++) {
        const cx = L + w * (k + 0.5);
        [[ramp_.g[k], tuned.gamma[k], cx - bw - 1, 'bar-p'], [ramp_.b[k], tuned.beta[k], cx + 1, 'bar-n']].forEach(([v, t, x, fill]) => {
          el('rect', { x, y: Y(v), width: bw, height: Math.max(B - Y(v), 0.5), class: fill }, anglesSvg);
          if (v > top) el('polygon', { points: `${x},${TOP + 6} ${x + bw},${TOP + 6} ${x + bw / 2},${TOP - 1}`, class: 'clipmark' }, anglesSvg);
          el('line', { x1: x - 3, x2: x + bw + 3, y1: Y(t), y2: Y(t), class: 'tick' }, anglesSvg);
        });
        txt(anglesSvg, cx, B + 14, String(k + 1), 'lbl');
      }
      txt(anglesSvg, (L + R) / 2, B + 27, 'layer k', 'lbl');
    }

    function drawCurve(p, T, here, tunedP) {
      curveSvg.textContent = '';
      const L = 34, R = 290, TOP = 10, B = 172;
      const X = (t) => L + (R - L) * t / TMAX, Y = (v) => B - (B - TOP) * v;
      [0, 0.5, 1].forEach((v) => { el('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'grid' }, curveSvg); txt(curveSvg, L - 6, Y(v) + 4, v.toFixed(1), 'lbl', 'end'); });
      [0, 5, 10, 15, 20].forEach((t) => txt(curveSvg, X(t), B + 14, String(t), 'lbl'));
      txt(curveSvg, (L + R) / 2, B + 27, 'total time T', 'lbl');
      const pts = (arr) => arr.map(([t, v]) => `${X(t).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
      el('line', { x1: L, x2: R, y1: Y(6 / 64), y2: Y(6 / 64), class: 'uni' }, curveSvg);
      el('polyline', { points: pts(fine), class: 'fine' }, curveSvg);
      const lim = sliceLimit(p);
      const inside = curve.filter(([t]) => t <= lim + 1e-9), outside = curve.filter(([t]) => t >= inside[inside.length - 1][0] - 1e-9);
      if (outside.length > 1) el('polyline', { points: pts(outside), class: 'trace faint' }, curveSvg);
      el('polyline', { points: pts(inside), class: 'trace' }, curveSvg);
      el('line', { x1: L, x2: R, y1: Y(tunedP), y2: Y(tunedP), class: 'qline' }, curveSvg);
      txt(curveSvg, R, Y(tunedP) - 5, `QAOA, p = ${p} tuned`, 'lbl-ink', 'end');
      el('circle', { cx: X(T), cy: Y(here), r: 4, class: 'dot' }, curveSvg);
    }

    function draw() {
      const p = +pSlider.value, T = tSlider.value / PER;
      if (!fine) fine = slideCurve(40, TMAX, 0.1);
      if (curveP !== p) { curve = slideCurve(p, TMAX, DT); curveP = p; }
      const tuned = TUNED[p - 1], here = ramp(p, T), best = qaoaRun(tuned.gamma, tuned.beta);
      byId('wkPOut').textContent = String(p);
      byId('wkTOut').textContent = T.toFixed(2);
      byId('wkSlideP').textContent = here.pmax.toFixed(3);
      byId('wkSlideE').textContent = here.mean.toFixed(2);
      byId('wkQaoaP').textContent = best.pmax.toFixed(3);
      byId('wkQaoaE').textContent = best.mean.toFixed(2);
      byId('wkFineP').textContent = ramp(40, T).pmax.toFixed(3);
      drawAngles(p, rampAngles(p, T), tuned);
      drawCurve(p, T, here.pmax, best.pmax);
    }
    const schedule = () => { if (pending) return; pending = true; requestAnimationFrame(() => { pending = false; draw(); }); };
    pSlider.addEventListener('input', schedule);
    tSlider.addEventListener('input', schedule);
    byId('wkBest').addEventListener('click', () => { tSlider.value = Math.round(bestT(+pSlider.value, TMAX, DT).T * PER); draw(); });
    draw();
  })();
