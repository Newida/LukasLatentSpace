

(() => {
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

  /* ---------- data: the slide on the prism (exact diagonalization) and tuned QAOA angles ---------- */
  const SLIDE = {"s":[0.0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12,0.13,0.14,0.15,0.16,0.17,0.18,0.19,0.2,0.21,0.22,0.23,0.24,0.25,0.26,0.27,0.28,0.29,0.3,0.31,0.32,0.33,0.34,0.35,0.36,0.37,0.38,0.39,0.4,0.41,0.42,0.43,0.44,0.45,0.46,0.47,0.48,0.49,0.5,0.51,0.52,0.53,0.54,0.55,0.56,0.57,0.58,0.59,0.6,0.61,0.62,0.63,0.64,0.65,0.66,0.67,0.68,0.69,0.7,0.71,0.72,0.73,0.74,0.75,0.76,0.77,0.78,0.79,0.8,0.81,0.82,0.83,0.84,0.85,0.86,0.87,0.88,0.89,0.9,0.91,0.92,0.93,0.94,0.95,0.96,0.97,0.98,0.99,1.0],"levels":[[-6.0,-2.0,-2.0,-2.0,2.0,2.0,2.0,6.0],[-5.9851,-2.0367,-2.0181,-2.0002,1.9233,1.9419,1.9599,5.8951],[-5.9702,-2.0734,-2.0362,-2.0006,1.8466,1.8838,1.9198,5.7902],[-5.9555,-2.1101,-2.0544,-2.0011,1.7699,1.8257,1.8799,5.6855],[-5.9409,-2.1468,-2.0725,-2.0016,1.6932,1.7676,1.8401,5.5809],[-5.9265,-2.1834,-2.0907,-2.0024,1.6165,1.7096,1.8004,5.4765],[-5.9121,-2.2201,-2.1089,-2.0032,1.5397,1.6515,1.7608,5.3722],[-5.8979,-2.2567,-2.1271,-2.0042,1.463,1.5935,1.7214,5.268],[-5.8839,-2.2934,-2.1453,-2.0053,1.3863,1.5355,1.682,5.164],[-5.8699,-2.33,-2.1635,-2.0066,1.3096,1.4775,1.6428,5.0601],[-5.8561,-2.3666,-2.1817,-2.008,1.2329,1.4195,1.6037,4.9564],[-5.8425,-2.4032,-2.2,-2.0096,1.1562,1.3615,1.5647,4.8528],[-5.829,-2.4398,-2.2183,-2.0113,1.0795,1.3036,1.5259,4.7494],[-5.8157,-2.4764,-2.2366,-2.0133,1.0028,1.2456,1.4871,4.6462],[-5.8025,-2.5129,-2.2549,-2.0154,0.9262,1.1877,1.4485,4.5432],[-5.7895,-2.5494,-2.2732,-2.0177,0.8495,1.1298,1.4101,4.4404],[-5.7767,-2.5859,-2.2915,-2.0202,0.7729,1.0719,1.3717,4.3378],[-5.764,-2.6224,-2.3099,-2.0229,0.6963,1.014,1.3335,4.2354],[-5.7516,-2.6588,-2.3283,-2.0259,0.6197,0.9562,1.2954,4.1332],[-5.7393,-2.6952,-2.3467,-2.029,0.5431,0.8983,1.2574,4.0313],[-5.7272,-2.7316,-2.3651,-2.0324,0.4666,0.8405,1.2196,3.9296],[-5.7153,-2.7679,-2.3836,-2.0361,0.3901,0.7827,1.1818,3.8282],[-5.7036,-2.8042,-2.4021,-2.04,0.3137,0.725,1.1442,3.7271],[-5.6921,-2.8404,-2.4206,-2.0442,0.2373,0.6672,1.1067,3.6262],[-5.6809,-2.8766,-2.4392,-2.0487,0.1609,0.6095,1.0693,3.5257],[-5.6699,-2.9127,-2.4578,-2.0535,0.0846,0.5518,1.032,3.4255],[-5.6591,-2.9488,-2.4764,-2.0587,0.0084,0.4941,0.9948,3.3256],[-5.6486,-2.9849,-2.495,-2.0641,-0.0677,0.4365,0.9577,3.2261],[-5.6384,-3.0208,-2.5137,-2.07,-0.1437,0.3789,0.9207,3.127],[-5.6284,-3.0567,-2.5325,-2.0762,-0.2197,0.3213,0.8837,3.0284],[-5.6187,-3.0926,-2.5513,-2.0828,-0.2955,0.2638,0.8468,2.9302],[-5.6092,-3.1283,-2.5701,-2.0898,-0.3712,0.2063,0.8099,2.8324],[-5.6001,-3.164,-2.589,-2.0972,-0.4467,0.1488,0.773,2.7352],[-5.5913,-3.1996,-2.6079,-2.1052,-0.5221,0.0914,0.7361,2.6386],[-5.5829,-3.2351,-2.6269,-2.1136,-0.5973,0.034,0.6992,2.5426],[-5.5747,-3.2705,-2.646,-2.1226,-0.6722,-0.0234,0.6622,2.4472],[-5.567,-3.3058,-2.6651,-2.1321,-0.7469,-0.0807,0.6251,2.3525],[-5.5596,-3.3409,-2.6844,-2.1423,-0.8213,-0.1379,0.5878,2.2586],[-5.5526,-3.376,-2.7037,-2.1531,-0.8954,-0.1951,0.5503,2.1656],[-5.546,-3.4109,-2.7231,-2.1646,-0.9691,-0.2522,0.5125,2.0734],[-5.5398,-3.4457,-2.7426,-2.177,-1.0424,-0.3093,0.4745,1.9823],[-5.5341,-3.4803,-2.7623,-2.1901,-1.1151,-0.3663,0.436,1.8922],[-5.5288,-3.5148,-2.782,-2.2042,-1.1873,-0.4232,0.397,1.8034],[-5.524,-3.5491,-2.8019,-2.2192,-1.2589,-0.4801,0.3574,1.7159],[-5.5198,-3.5833,-2.822,-2.2354,-1.3296,-0.5368,0.3171,1.6298],[-5.516,-3.6173,-2.8423,-2.2528,-1.3994,-0.5935,0.2761,1.5453],[-5.5128,-3.6511,-2.8628,-2.2716,-1.4682,-0.6501,0.234,1.4626],[-5.5102,-3.6846,-2.8835,-2.2919,-1.5358,-0.7066,0.1909,1.3818],[-5.5083,-3.718,-2.9045,-2.3139,-1.602,-0.7629,0.1465,1.303],[-5.5069,-3.7512,-2.9258,-2.3377,-1.6665,-0.8191,0.1007,1.2266],[-5.5062,-3.7841,-2.9474,-2.3637,-1.7292,-0.8752,0.0533,1.1526],[-5.5063,-3.8168,-2.9695,-2.3919,-1.7898,-0.9311,0.0042,1.0812],[-5.507,-3.8493,-2.9921,-2.4226,-1.848,-0.9869,-0.0467,1.0126],[-5.5085,-3.8815,-3.0153,-2.456,-1.9036,-1.0424,-0.0996,0.9469],[-5.5109,-3.9134,-3.0391,-2.492,-1.9566,-1.0978,-0.1546,0.8843],[-5.514,-3.9451,-3.0637,-2.5306,-2.0067,-1.1529,-0.2117,0.8248],[-5.5181,-3.9765,-3.0893,-2.5718,-2.0541,-1.2078,-0.271,0.7685],[-5.523,-4.0077,-3.116,-2.6151,-2.0988,-1.2624,-0.3324,0.7154],[-5.5289,-4.0386,-3.1441,-2.6602,-2.1412,-1.3167,-0.3958,0.6654],[-5.5357,-4.0693,-3.1738,-2.7064,-2.1815,-1.3706,-0.4611,0.6184],[-5.5436,-4.0998,-3.2054,-2.7532,-2.22,-1.4242,-0.5282,0.5744],[-5.5525,-4.1301,-3.2391,-2.8,-2.2572,-1.4774,-0.597,0.5332],[-5.5626,-4.1602,-3.2752,-2.846,-2.2934,-1.5301,-0.6672,0.4946],[-5.5737,-4.1901,-3.3141,-2.8908,-2.3289,-1.5823,-0.7386,0.4585],[-5.586,-4.22,-3.3558,-2.9338,-2.3641,-1.6339,-0.8111,0.4247],[-5.5995,-4.2499,-3.4004,-2.9747,-2.3992,-1.6849,-0.8845,0.3931],[-5.6142,-4.2799,-3.4479,-3.0133,-2.4345,-1.7353,-0.9585,0.3636],[-5.6302,-4.31,-3.4978,-3.0497,-2.4701,-1.785,-1.0331,0.3359],[-5.6475,-4.3404,-3.55,-3.0839,-2.5063,-1.8339,-1.108,0.31],[-5.666,-4.3712,-3.604,-3.1162,-2.5432,-1.8819,-1.1831,0.2856],[-5.6859,-4.4025,-3.6593,-3.1467,-2.581,-1.9291,-1.2582,0.2629],[-5.7072,-4.4346,-3.7155,-3.1758,-2.6198,-1.9754,-1.3332,0.2415],[-5.7298,-4.4677,-3.772,-3.2037,-2.6597,-2.0207,-1.4079,0.2214],[-5.7538,-4.5019,-3.8285,-3.2306,-2.7007,-2.065,-1.4823,0.2026],[-5.7792,-4.5375,-3.8844,-3.2566,-2.7428,-2.1084,-1.5561,0.185],[-5.806,-4.5747,-3.9394,-3.282,-2.7862,-2.1507,-1.6294,0.1685],[-5.8343,-4.6139,-3.9931,-3.3069,-2.8308,-2.1921,-1.702,0.153],[-5.864,-4.6551,-4.0452,-3.3314,-2.8766,-2.2325,-1.7737,0.1385],[-5.8952,-4.6986,-4.0955,-3.3557,-2.9234,-2.2719,-1.8446,0.125],[-5.9278,-4.7446,-4.1438,-3.3798,-2.9714,-2.3105,-1.9144,0.1123],[-5.962,-4.793,-4.19,-3.4039,-3.0203,-2.3482,-1.9831,0.1005],[-5.9977,-4.8438,-4.2342,-3.428,-3.0702,-2.3851,-2.0506,0.0895],[-6.0349,-4.8969,-4.2765,-3.4522,-3.1208,-2.4213,-2.1168,0.0793],[-6.0737,-4.9521,-4.317,-3.4766,-3.172,-2.4568,-2.1816,0.0698],[-6.1141,-5.0092,-4.356,-3.5013,-3.2238,-2.4917,-2.245,0.0611],[-6.1561,-5.068,-4.3938,-3.5264,-3.2759,-2.526,-2.3068,0.0531],[-6.1998,-5.1282,-4.4307,-3.5519,-3.3282,-2.5598,-2.367,0.0457],[-6.2452,-5.1894,-4.467,-3.5779,-3.3807,-2.5932,-2.4255,0.0389],[-6.2923,-5.2516,-4.5031,-3.6045,-3.433,-2.6261,-2.4822,0.0328],[-6.3411,-5.3143,-4.5392,-3.6319,-3.485,-2.6587,-2.537,0.0272],[-6.3917,-5.3775,-4.5756,-3.66,-3.5367,-2.6909,-2.5898,0.0222],[-6.4442,-5.4408,-4.6125,-3.6891,-3.5877,-2.7228,-2.6407,0.0178],[-6.4984,-5.5043,-4.6503,-3.719,-3.638,-2.7545,-2.6894,0.0139],[-6.5546,-5.5676,-4.689,-3.75,-3.6874,-2.7859,-2.736,0.0105],[-6.6126,-5.6306,-4.729,-3.7821,-3.7358,-2.817,-2.7804,0.0077],[-6.6725,-5.6934,-4.7703,-3.8154,-3.7831,-2.848,-2.8226,0.0053],[-6.7343,-5.7557,-4.813,-3.8498,-3.8292,-2.8787,-2.8625,0.0033],[-6.798,-5.8176,-4.8573,-3.8855,-3.8739,-2.9093,-2.9002,0.0019],[-6.8635,-5.8789,-4.9032,-3.9224,-3.9173,-2.9397,-2.9357,0.0008],[-6.9309,-5.9397,-4.9508,-3.9606,-3.9593,-2.9699,-2.9689,0.0002],[-7.0,-6.0,-5.0,-4.0,-4.0,-3.0,-3.0,0.0]],"dists":[[0.0313,0.0,0.0,0.2187,0.2813,0.1875,0.1875,0.0937],[0.0305,0.0,0.0,0.2171,0.2805,0.188,0.1889,0.0949],[0.0299,0.0,0.0,0.2154,0.2798,0.1884,0.1904,0.0962],[0.0292,0.0,0.0,0.2137,0.279,0.1889,0.1919,0.0974],[0.0285,0.0,0.0,0.212,0.2782,0.1893,0.1934,0.0987],[0.0278,0.0,0.0,0.2102,0.2773,0.1897,0.1949,0.1001],[0.0271,0.0,0.0,0.2084,0.2764,0.1902,0.1965,0.1014],[0.0264,0.0,0.0,0.2066,0.2754,0.1906,0.1981,0.1029],[0.0257,0.0,0.0,0.2047,0.2744,0.191,0.1998,0.1043],[0.0251,0.0,0.0,0.2028,0.2734,0.1913,0.2015,0.1059],[0.0244,0.0,0.0,0.2009,0.2723,0.1917,0.2033,0.1074],[0.0238,0.0,0.0,0.1989,0.2711,0.192,0.205,0.1091],[0.0231,0.0,0.0,0.197,0.27,0.1924,0.2069,0.1107],[0.0225,0.0,0.0,0.1949,0.2687,0.1927,0.2087,0.1125],[0.0218,0.0,0.0,0.1929,0.2674,0.193,0.2107,0.1143],[0.0212,0.0,0.0,0.1908,0.2661,0.1932,0.2126,0.1161],[0.0206,0.0,0.0,0.1886,0.2646,0.1935,0.2146,0.1181],[0.0199,0.0,0.0,0.1865,0.2632,0.1937,0.2167,0.1201],[0.0193,0.0,0.0,0.1843,0.2616,0.1939,0.2188,0.1221],[0.0187,0.0,0.0,0.182,0.26,0.194,0.221,0.1243],[0.0181,0.0,0.0,0.1797,0.2583,0.1941,0.2232,0.1265],[0.0175,0.0,0.0,0.1774,0.2566,0.1942,0.2255,0.1288],[0.0169,0.0,0.0,0.175,0.2547,0.1943,0.2278,0.1312],[0.0163,0.0,0.0,0.1726,0.2528,0.1943,0.2302,0.1337],[0.0157,0.0,0.0,0.1702,0.2508,0.1942,0.2326,0.1363],[0.0152,0.0,0.0,0.1677,0.2488,0.1942,0.2352,0.1391],[0.0146,0.0,0.0,0.1652,0.2466,0.194,0.2377,0.1419],[0.014,0.0,0.0,0.1626,0.2444,0.1938,0.2404,0.1448],[0.0135,0.0,0.0,0.16,0.242,0.1936,0.2431,0.1479],[0.013,0.0,0.0,0.1573,0.2396,0.1933,0.2459,0.1511],[0.0124,0.0,0.0,0.1546,0.237,0.1929,0.2487,0.1544],[0.0119,0.0,0.0,0.1518,0.2344,0.1924,0.2516,0.1579],[0.0114,0.0,0.0,0.149,0.2316,0.1919,0.2546,0.1615],[0.0109,0.0,0.0,0.1461,0.2288,0.1913,0.2576,0.1653],[0.0104,0.0,0.0,0.1432,0.2258,0.1906,0.2608,0.1693],[0.0099,0.0,0.0,0.1402,0.2227,0.1898,0.264,0.1734],[0.0094,0.0,0.0,0.1372,0.2195,0.1889,0.2672,0.1777],[0.009,0.0,0.0,0.1342,0.2161,0.1879,0.2706,0.1823],[0.0085,0.0,0.0,0.1311,0.2127,0.1868,0.274,0.1871],[0.0081,0.0,0.0,0.1279,0.2091,0.1855,0.2774,0.192],[0.0076,0.0,0.0,0.1247,0.2053,0.1841,0.2809,0.1973],[0.0072,0.0,0.0,0.1214,0.2015,0.1826,0.2845,0.2027],[0.0068,0.0,0.0,0.1181,0.1974,0.181,0.2882,0.2085],[0.0064,0.0,0.0,0.1148,0.1933,0.1792,0.2918,0.2145],[0.006,0.0,0.0,0.1114,0.189,0.1772,0.2956,0.2208],[0.0056,0.0,0.0,0.1079,0.1845,0.1751,0.2993,0.2275],[0.0053,0.0,0.0,0.1044,0.1799,0.1728,0.3031,0.2344],[0.0049,0.0,0.0,0.1009,0.1752,0.1703,0.3069,0.2417],[0.0046,0.0,0.0,0.0974,0.1703,0.1676,0.3107,0.2494],[0.0043,0.0,0.0,0.0938,0.1653,0.1648,0.3144,0.2574],[0.0039,0.0,0.0,0.0902,0.1602,0.1617,0.3181,0.2659],[0.0036,0.0,0.0,0.0865,0.1549,0.1584,0.3218,0.2747],[0.0033,0.0,0.0,0.0828,0.1495,0.1549,0.3254,0.284],[0.0031,0.0,0.0,0.0792,0.144,0.1512,0.3288,0.2937],[0.0028,0.0,0.0,0.0755,0.1384,0.1472,0.3322,0.3039],[0.0026,0.0,0.0,0.0718,0.1327,0.1431,0.3353,0.3146],[0.0023,0.0,0.0,0.0681,0.1269,0.1387,0.3383,0.3257],[0.0021,0.0,0.0,0.0644,0.1211,0.1341,0.341,0.3373],[0.0019,0.0,0.0,0.0608,0.1152,0.1293,0.3434,0.3495],[0.0017,0.0,0.0,0.0572,0.1093,0.1243,0.3454,0.3621],[0.0015,0.0,0.0,0.0536,0.1033,0.1191,0.3471,0.3753],[0.0013,0.0,0.0,0.0501,0.0974,0.1138,0.3484,0.3889],[0.0012,0.0,0.0,0.0467,0.0916,0.1083,0.3492,0.4031],[0.001,0.0,0.0,0.0433,0.0858,0.1027,0.3495,0.4177],[0.0009,0.0,0.0,0.04,0.08,0.097,0.3491,0.4329],[0.0008,0.0,0.0,0.0368,0.0744,0.0912,0.3482,0.4485],[0.0007,0.0,0.0,0.0337,0.069,0.0854,0.3465,0.4646],[0.0006,0.0,0.0,0.0308,0.0637,0.0796,0.3442,0.4812],[0.0005,0.0,0.0,0.0279,0.0586,0.0738,0.341,0.4982],[0.0004,0.0,0.0,0.0252,0.0536,0.0681,0.3371,0.5155],[0.0004,0.0,0.0,0.0227,0.0489,0.0624,0.3323,0.5333],[0.0003,0.0,0.0,0.0203,0.0445,0.0569,0.3266,0.5514],[0.0002,0.0,0.0,0.018,0.0402,0.0516,0.3201,0.5698],[0.0002,0.0,0.0,0.0159,0.0363,0.0465,0.3126,0.5886],[0.0002,0.0,0.0,0.014,0.0326,0.0415,0.3042,0.6076],[0.0001,0.0,0.0,0.0122,0.0291,0.0369,0.2949,0.6268],[0.0001,0.0,0.0,0.0105,0.0259,0.0325,0.2847,0.6463],[0.0001,0.0,0.0,0.009,0.023,0.0283,0.2736,0.666],[0.0001,0.0,0.0,0.0077,0.0203,0.0245,0.2617,0.6858],[0.0,0.0,0.0,0.0065,0.0178,0.021,0.249,0.7057],[0.0,0.0,0.0,0.0054,0.0156,0.0178,0.2355,0.7258],[0.0,0.0,0.0,0.0044,0.0135,0.0149,0.2213,0.7458],[0.0,0.0,0.0,0.0036,0.0117,0.0123,0.2065,0.7659],[0.0,0.0,0.0,0.0029,0.0101,0.01,0.1912,0.7858],[0.0,0.0,0.0,0.0023,0.0086,0.008,0.1754,0.8056],[0.0,0.0,0.0,0.0018,0.0073,0.0063,0.1594,0.8252],[0.0,0.0,0.0,0.0014,0.0062,0.0049,0.1432,0.8443],[0.0,0.0,0.0,0.001,0.0052,0.0037,0.1271,0.8631],[0.0,0.0,0.0,0.0007,0.0043,0.0027,0.1111,0.8812],[0.0,0.0,0.0,0.0005,0.0035,0.0019,0.0956,0.8985],[0.0,0.0,0.0,0.0004,0.0028,0.0013,0.0806,0.915],[0.0,0.0,0.0,0.0002,0.0022,0.0009,0.0663,0.9304],[0.0,0.0,0.0,0.0001,0.0017,0.0005,0.0531,0.9445],[0.0,0.0,0.0,0.0001,0.0013,0.0003,0.041,0.9573],[0.0,0.0,0.0,0.0,0.0009,0.0002,0.0303,0.9686],[0.0,0.0,0.0,0.0,0.0006,0.0001,0.0211,0.9782],[0.0,0.0,0.0,0.0,0.0004,0.0,0.0135,0.9861],[0.0,0.0,0.0,0.0,0.0002,0.0,0.0075,0.9923],[0.0,0.0,0.0,0.0,0.0001,0.0,0.0033,0.9966],[0.0,0.0,0.0,0.0,0.0,0.0,0.0008,0.9992],[0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0]]};
  const TUNED = [{"p":1,"gamma":[0.5703],"beta":[0.3482]},{"p":2,"gamma":[0.5023,0.9168],"beta":[0.4784,0.2859]},{"p":3,"gamma":[0.4085,0.8575,1.0448],"beta":[0.5067,0.343,0.1692]},{"p":4,"gamma":[0.3787,0.7705,1.0286,1.2681],"beta":[0.5333,0.3663,0.2,0.0941]},{"p":5,"gamma":[0.2782,0.6604,0.8148,1.1269,1.2834],"beta":[0.5377,0.4157,0.2777,0.1408,0.09]},{"p":6,"gamma":[0.215,0.4653,0.6146,0.8149,1.1226,1.1914],"beta":[0.5104,0.3522,0.3189,0.2115,0.1172,0.0789]},{"p":7,"gamma":[0.1828,0.4216,0.5283,0.7025,0.9151,1.1951,1.1411],"beta":[0.5413,0.375,0.3122,0.2702,0.169,0.1051,0.0559]},{"p":8,"gamma":[0.16,0.3747,0.4979,0.587,0.764,1.0003,1.1525,1.1659],"beta":[0.5235,0.3738,0.3019,0.2527,0.1953,0.1228,0.0824,0.0281]}];

  /* ---------- engine: exact simulation on the prism (expects SLIDE and TUNED) ---------- */
  const PRISM = (() => {
    const n = 6, N = 64;
    const E = [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [0, 3], [1, 4], [2, 5]];
    const C = new Float64Array(N);
    for (let x = 0; x < N; x++) for (const [i, j] of E) if (((x >> i) & 1) !== ((x >> j) & 1)) C[x] += 1;
    let Cmax = 0; for (let x = 0; x < N; x++) Cmax = Math.max(Cmax, C[x]);
    return { n, N, E, C, Cmax };
  })();

  // Layer k applies exp(-i gamma_k H_C) = exp(i gamma_k C), then exp(-i beta_k H_B) = exp(i beta_k sum_j X_j).
  function qaoaRun(gammas, betas) {
    const { n, N, C, Cmax } = PRISM;
    const re = new Float64Array(N).fill(1 / Math.sqrt(N)), im = new Float64Array(N);
    for (let k = 0; k < gammas.length; k++) {
      for (let x = 0; x < N; x++) {
        const c = Math.cos(gammas[k] * C[x]), s = Math.sin(gammas[k] * C[x]), r = re[x], m = im[x];
        re[x] = r * c - m * s; im[x] = r * s + m * c;
      }
      const cb = Math.cos(betas[k]), sb = Math.sin(betas[k]);
      for (let j = 0; j < n; j++) {
        const bit = 1 << j;
        for (let x = 0; x < N; x++) {
          if (x & bit) continue;
          const y = x | bit, ar = re[x], ai = im[x], br = re[y], bi = im[y];
          re[x] = cb * ar - sb * bi; im[x] = cb * ai + sb * br;
          re[y] = cb * br - sb * ai; im[y] = cb * bi + sb * ar;
        }
      }
    }
    let mean = 0, pmax = 0;
    for (let x = 0; x < N; x++) { const pr = re[x] * re[x] + im[x] * im[x]; mean += pr * C[x]; if (C[x] === Cmax) pmax += pr; }
    return { mean, pmax };
  }

  // The chopped slide: p pieces of length T / p, with s_k = (k - 1/2) / p in the middle of piece k.
  function rampAngles(p, T) {
    const g = [], b = [];
    for (let k = 1; k <= p; k++) { const s = (k - 0.5) / p; g.push(s * T / p); b.push((1 - s) * T / p); }
    return { g, b };
  }
  function ramp(p, T) { const { g, b } = rampAngles(p, T); return qaoaRun(g, b); }

  // Pieces longer than pi/2 make the mixer angle wrap around; beyond that the circuit is no slide anymore.
  const sliceLimit = (p) => p * Math.PI / 2;
  function slideCurve(p, Tmax, dT) {
    const pts = [];
    for (let T = 0; T <= Tmax + 1e-9; T += dT) pts.push([T, ramp(p, T).pmax]);
    return pts;
  }
  function bestT(p, Tmax, dT) {
    let best = { T: 0, pmax: -1 };
    for (let T = 0; T <= Math.min(Tmax, sliceLimit(p)) + 1e-9; T += dT) {
      const v = ramp(p, T).pmax;
      if (v > best.pmax) best = { T, pmax: v };
    }
    return best;
  }

  const slideStats = (k) => {
    const d = SLIDE.dists[k];
    let mean = 0; for (let c = 0; c < d.length; c++) mean += c * d[c];
    return { gap: SLIDE.levels[k][1] - SLIDE.levels[k][0], pmax: d[PRISM.Cmax], mean };
  };
  const MIN_GAP = (() => {
    let best = { gap: Infinity, s: 0 };
    SLIDE.s.forEach((s, k) => { const g = SLIDE.levels[k][1] - SLIDE.levels[k][0]; if (g < best.gap) best = { gap: g, s }; });
    return best;
  })();

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
})();
