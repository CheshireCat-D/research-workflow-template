'use strict';
(() => {
  const atlas = document.querySelector('.atlas-layout');
  const links = Array.from(document.querySelectorAll('#skill-nav [data-key]'));
  const skills = links.map(link => {
    const key = link.dataset.key;
    const article = document.getElementById('rw-' + key);
    return {
      key,
      title: link.textContent,
      detail: article.querySelector('h3').textContent,
      article,
      link
    };
  });
  const markers = new Map();
  const caption = document.getElementById('map-caption');
  let selected;
  function select(key) {
    const next = skills.find(skill => skill.key === key);
    if (!next) return;
    selected = next;
    for (const skill of skills) {
      const active = skill === next;
      skill.article.hidden = !active;
      if (active)
        skill.link.setAttribute('aria-current', 'true');
      else
        skill.link.removeAttribute('aria-current');
      markers.get(skill.key)?.setAttribute('aria-pressed', String(active));
    }
    if (markers.size) {
      const inspect = document.createElement('a');
      inspect.href = '#skills';
      inspect.textContent = 'Inspect skill ↓';
      caption.replaceChildren(
          document.createTextNode(next.title + ' · ' + next.detail + '  '), inspect);
    }
  }
  function selectFromHash() {
    const match = skills.find(skill => '#' + skill.article.id === location.hash);
    if (match)
      select(match.key);
    else if (!selected)
      select(skills[0].key);
  }
  atlas.classList.add('enhanced');
  links.forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    select(link.dataset.key);
    if (location.protocol !== 'file:') history.replaceState(null, '', link.hash);
  }));
  selectFromHash();
  window.addEventListener('hashchange', selectFromHash);

  const canvas = document.getElementById('universe');
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const map = document.getElementById('map');
  const buttons = document.getElementById('markers');
  const toggle = document.getElementById('motion');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const TAU = Math.PI * 2;
  const geometry = [
    [.22, 2.66, 17, [123, 210, 187], true], [.44, -2.63, 11, [131, 164, 202], false],
    [.36, -1.94, 14, [147, 137, 204], false], [.41, -1.14, 10, [217, 153, 84], false],
    [.32, -.20, 12, [126, 178, 188], false], [.448, .49, 17, [177, 136, 190], true],
    [.28, 1.02, 10, [131, 185, 217], false], [.46, 1.53, 16, [206, 144, 113], false],
    [.415, 2.06, 10, [174, 176, 130], false]
  ];
  function randomSource(seed) {
    let state = seed;
    return () => {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }
  const random = randomSource(314159);
  const lattice = Array.from({length: 256 * 256}, () => random());
  function noise(x, y) {
    const ix = Math.floor(x), iy = Math.floor(y);
    let u = x - ix, v = y - iy;
    u = u * u * (3 - 2 * u);
    v = v * v * (3 - 2 * v);
    const a = lattice[((iy & 255) << 8) | (ix & 255)];
    const b = lattice[((iy & 255) << 8) | ((ix + 1) & 255)];
    const c = lattice[(((iy + 1) & 255) << 8) | (ix & 255)];
    const d = lattice[(((iy + 1) & 255) << 8) | ((ix + 1) & 255)];
    return (a + (b - a) * u) * (1 - v) + (c + (d - c) * u) * v;
  }
  function makeSphere(color, seed, striped, sun = false) {
    const texture = document.createElement('canvas');
    const size = 128;
    texture.width = texture.height = size;
    const painter = texture.getContext('2d');
    const pixels = painter.createImageData(size, size);
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const nx = (2 * x + 1) / size - 1, ny = (2 * y + 1) / size - 1;
        const rr = nx * nx + ny * ny;
        if (rr >= 1) continue;
        const nz = Math.sqrt(1 - rr);
        const longitude = Math.atan2(nx, nz), latitude = Math.asin(ny);
        const broad = noise(seed + longitude * 3, latitude * 4 + seed);
        const fine = noise(seed + longitude * 19, latitude * 23 + seed);
        const band = Math.sin(latitude * 25 + broad * 4 + seed);
        const grain = .62 * broad + .27 * fine + .11 * noise(nx * 100, ny * 100);
        let value = .72 + .5 * grain + (striped ? .12 * band : .12 * Math.sin(grain * 14));
        let light = .13 + .95 * Math.max(0, -.59 * nx - .46 * ny + .67 * nz);
        if (sun) {
          value = .81 + .2 * grain + .08 * Math.sin(12 * grain);
          light = .74 + .28 * nz;
        }
        const rim = Math.pow(1 - nz, 4.2) * (sun ? .15 : .23);
        const i = (y * size + x) * 4;
        for (let channel = 0; channel < 3; channel++) {
          pixels.data[i + channel] =
              color[channel] * value * light + rim * [120, 163, 178][channel];
        }
        pixels.data[i + 3] = Math.min(255, (1 - Math.sqrt(rr)) * size * 185);
      }
    }
    painter.putImageData(pixels, 0, 0);
    return texture;
  }
  const planets = skills.map((skill, i) => {
    const [orbit, phase, radius, color, ring] = geometry[i];
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'marker';
    button.setAttribute('aria-label', skill.title + ' · ' + skill.detail);
    button.setAttribute('aria-controls', skill.article.id);
    const label = document.createElement('span');
    label.className = 'marker-label';
    label.textContent = skill.title;
    button.append(label);
    buttons.append(button);
    button.addEventListener('click', () => select(skill.key));
    markers.set(skill.key, button);
    return {
      key: skill.key,
      orbit,
      phase,
      radius,
      ring,
      color,
      button,
      sprite: makeSphere(color, i * 11 + 1, ring || i === 7)
    };
  });
  const star = makeSphere([255, 206, 125], 7, false, true);
  const rubble = Array.from({length: 220}, () => ({
                                             a: .355 + (random() - .5) * .029,
                                             p: random() * TAU,
                                             radius: .45 + Math.pow(random(), 3) * 2.8,
                                             height: (random() - .5) * .028,
                                             angle: random() * TAU,
                                             speed: .015 + random() * .007,
                                             light: Math.floor(76 + random() * 92)
                                           }));
  const stars = Array.from(
      {length: 305}, () => ({
                       x: random(),
                       y: random(),
                       r: .25 + Math.pow(random(), 4) * 1.75,
                       color:
                           [[162, 205, 255], [251, 198, 140], [209, 219, 251],
                            [237, 239, 249]][Math.floor(random() * 4)],
                       alpha: .34 + random() * .63,
                       phase: random() * TAU
                     }));
  const cloud = document.createElement('canvas');
  cloud.width = 384;
  cloud.height = 234;
  const painter = cloud.getContext('2d'), mist = painter.createImageData(cloud.width, cloud.height);
  for (let y = 0; y < cloud.height; y++) {
    for (let x = 0; x < cloud.width; x++) {
      const u = x / cloud.width, v = y / cloud.height, n = noise(u * 4 + 3, v * 5 + 7);
      const lane = Math.exp(-Math.pow((v - .74 + u * .54 + (n - .5) * .24) / .23, 2));
      const ridge = lane *
          (.35 * n + .23 * noise(u * 12, v * 13) + .20 * noise(u * 29, v * 31) +
           .10 * noise(u * 75, v * 62));
      const d = (y * cloud.width + x) * 4;
      mist.data[d] = 9 + ridge * (18 + 35 * u);
      mist.data[d + 1] = 14 + ridge * (30 - 10 * u);
      mist.data[d + 2] = 25 + ridge * 65;
      mist.data[d + 3] = 255;
    }
  }
  painter.putImageData(mist, 0, 0);
  let width = 1, height = 1, scale = 1, clock = 0, last = 0, frame = 0, visible = true;
  let paused = preference.matches;
  function position(radius, phase) {
    const a = radius * width, b = a * .47;
    return [
      width * .5 + Math.cos(phase) * a * .952 + Math.sin(phase) * b * .305,
      height * .50 - Math.cos(phase) * a * .305 + Math.sin(phase) * b * .952
    ];
  }
  function glow(x, y, r, stops) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    for (const [offset, color] of stops) g.addColorStop(offset, color);
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  function drawRings(x, y, r, color, front) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(-.33);
    ctx.scale(1, .28);
    for (let i = 0; i < 13; i++) {
      const alpha = (i === 4 || i === 8) ? .08 : .22 + .16 * Math.sin(i * 1.4);
      ctx.strokeStyle = 'rgba(' + color.join(',') + ',' + alpha + ')';
      ctx.lineWidth = r * .038;
      ctx.beginPath();
      ctx.arc(0, 0, r * (1.25 + i * .044), 0, front ? Math.PI : TAU);
      ctx.stroke();
    }
    ctx.restore();
  }
  function draw() {
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(cloud, 0, 0, width, height);
    for (const s of stars) {
      const twinkle = .82 + .18 * Math.sin(clock * .46 + s.phase);
      const x = s.x * width;
      const y = s.y * height;
      const rgb = s.color.join(',');
      if (s.r > 1.63) {
        glow(x, y, 5 * scale, [[0, 'rgba(' + rgb + ',.6)'], [1, 'rgba(' + rgb + ',0)']]);
      }
      ctx.fillStyle = 'rgba(' + rgb + ',' + (s.alpha * twinkle) + ')';
      ctx.beginPath();
      ctx.arc(x, y, s.r * scale, 0, TAU);
      ctx.fill();
      if (s.r > 1.90) {
        ctx.fillRect(x - 4 * scale, y - .35 * scale, 8 * scale, .7 * scale);
        ctx.fillRect(x - .35 * scale, y - 3 * scale, .7 * scale, 6 * scale);
      }
    }
    for (const p of planets) {
      ctx.beginPath();
      ctx.ellipse(width * .5, height * .5, p.orbit * width, p.orbit * width * .47, -.31, 0, TAU);
      ctx.strokeStyle = selected.key === p.key ? 'rgba(129,222,211,.52)' : 'rgba(139,161,194,.24)';
      ctx.lineWidth = .72 * scale;
      ctx.stroke();
    }
    for (const rock of rubble) {
      const [x, base] = position(rock.a, rock.p + clock * rock.speed);
      const y = base + rock.height * width, r = rock.radius * scale;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rock.angle + clock * .03);
      ctx.fillStyle = 'rgb(' + rock.light + ',' + (rock.light - 5) + ',' + (rock.light + 1) + ')';
      ctx.beginPath();
      ctx.moveTo(-r, -r * .14);
      ctx.lineTo(-r * .4, -r * .62);
      ctx.lineTo(r * .62, -r * .46);
      ctx.lineTo(r, r * .12);
      ctx.lineTo(r * .28, r * .56);
      ctx.lineTo(-r * .68, r * .4);
      ctx.fill();
      if (r > 1.4) {
        ctx.fillStyle = '#2d303e';
        ctx.beginPath();
        ctx.moveTo(-r * .68, r * .4);
        ctx.lineTo(r * .28, r * .56);
        ctx.lineTo(r, r * .12);
        ctx.lineTo(r * .1, -r * .05);
        ctx.fill();
      }
      ctx.restore();
    }
    const cx = width * .5, cy = height * .5, sr = 18 * scale;
    glow(cx, cy, 104 * scale, [
      [0, '#fff1ba'], [.14, '#ffcc80d0'], [.28, '#fba86165'], [.55, '#c9693a26'], [1, '#bc744400']
    ]);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-.18);
    for (let i = 0; i < 26; i++) {
      const angle = i * TAU / 26 + Math.sin(i * 3.4) * .07;
      const length = sr * (1.45 + .27 * Math.sin(i * 14.23 + clock * .24));
      ctx.strokeStyle = 'rgba(255,184,96,.19)';
      ctx.lineWidth = scale;
      ctx.beginPath();
      ctx.moveTo(Math.cos(angle) * sr * .87, Math.sin(angle) * sr * .87);
      ctx.quadraticCurveTo(
          Math.cos(angle + .07) * length * .90, Math.sin(angle + .07) * length * .90,
          Math.cos(angle) * length, Math.sin(angle) * length);
      ctx.stroke();
    }
    ctx.restore();
    ctx.drawImage(star, cx - sr, cy - sr, 2 * sr, 2 * sr);
    for (const p of planets) {
      const angle = p.phase + clock * (.006 + .002 / p.orbit);
      const [x, y] = position(p.orbit, angle), r = p.radius * scale;
      glow(
          x, y, r * 1.38,
          [[0, 'rgba(' + p.color.join(',') + ',.18)'], [1, 'rgba(' + p.color.join(',') + ',0)']]);
      if (p.ring) drawRings(x, y, r, p.color, false);
      ctx.drawImage(p.sprite, x - r, y - r, 2 * r, 2 * r);
      if (p.ring) drawRings(x, y, r, p.color, true);
      p.button.style.left = x + 'px';
      p.button.style.top = y + 'px';
      p.button.style.setProperty('--radius', r + 'px');
    }
  }
  function tick(t) {
    frame = 0;
    if (paused || !visible || document.hidden) return;
    if (!last) last = t;
    if (t - last >= 33) {
      clock += Math.min((t - last) / 1000, .16);
      last = t;
      draw();
    }
    frame = requestAnimationFrame(tick);
  }
  function sync() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    last = 0;
    toggle.textContent = paused ? 'Play motion' : 'Pause motion';
    toggle.classList.toggle('is-paused', paused);
    draw();
    if (!paused && visible && !document.hidden) frame = requestAnimationFrame(tick);
  }
  function resize() {
    width = map.clientWidth;
    height = map.clientHeight;
    if (!width || !height) return;
    scale = Math.max(.53, Math.min(1.65, width / 620));
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    paused = !paused;
    sync();
  });
  preference.addEventListener('change', event => {
    paused = event.matches;
    sync();
  });
  document.addEventListener('visibilitychange', sync);
  if ('IntersectionObserver' in window)
    new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      sync();
    }).observe(map);
  if ('ResizeObserver' in window)
    new ResizeObserver(resize).observe(map);
  else
    window.addEventListener('resize', resize);
  document.addEventListener('click', () => {
    if (paused) draw();
  });
  map.classList.add('ready');
  select(selected.key);
  resize();
  sync();
})();
