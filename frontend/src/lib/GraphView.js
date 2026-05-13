import { forceSimulation, forceLink, forceManyBody, forceCollide } from 'd3-force';

export const TYPE_COLORS = {
  Ninjutsu: '#FF6B35',
  Taijutsu: '#2E8B57',
  Genjutsu: '#9932CC',
  'Kekkei Genkai': '#DC143C',
  Hiden: '#4169E1',
  Dōjutsu: '#FF4444',
  Kenjutsu: '#A0A0A0',
  Fūinjutsu: '#FFD700',
  Senjutsu: '#32CD32',
  Kinjutsu: '#8B0000',
  Bukijutsu: '#708090',
  'Medical Ninjutsu': '#00CED1',
  'Space–Time Ninjutsu': '#9400D3',
  'Cooperation Ninjutsu': '#7CFC00',
  'Clone Techniques': '#FFA500',
  'Chakra Flow': '#00FFFF',
  Shurikenjutsu: '#B8860B',
  'Barrier Ninjutsu': '#1E90FF',
  'Collaboration Techniques': '#98FB98',
  'Chakra Absorption Techniques': '#FF69B4',
  Juinjutsu: '#4B0082',
  'Fighting Style': '#DAA520',
  Shinjutsu: '#DDA0DD',
  'Scientific Ninja Tool Techniques': '#00FA9A',
  'Kekkei Mōra': '#F0F0F0',
  'Reincarnation Ninjutsu': '#6A5ACD',
  'Regeneration Techniques': '#ADFF2F',
};

export function typeColor(t) {
  return TYPE_COLORS[t] ?? '#888';
}

export class GraphView {
  constructor(canvas, data, callbacks = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.nodes = data.nodes;
    this.edges = data.edges;
    this.callbacks = callbacks;

    // View transform
    this.tx = 0;
    this.ty = 0;
    this.scale = 1;

    // Smooth animation target
    this._atx = 0;
    this._aty = 0;
    this._asc = 1;
    this._animating = false;

    // State
    this.selected = null;
    this.hovered = null;
    this.highlighted = new Set();
    this.dimmed = false;
    this.showEdges = true;
    this.dirty = true;
    this._userInteracted = false;

    // Mouse screen position for tooltip
    this.mouseX = 0;
    this.mouseY = 0;

    // Filters
    this.activeTypes = new Set();
    this.activeRanks = new Set();
    this.activeChakras = new Set();
    this.searchQuery = '';
    this.visibleIds = new Set(this.nodes.map((n) => n.id));

    // Lookups
    this.nodeById = {};
    this.edgesByNodeId = {};
    this.nodes.forEach((n) => {
      this.nodeById[n.id] = n;
      this.edgesByNodeId[n.id] = [];
    });
    this.edges.forEach((e) => {
      this.edgesByNodeId[e.source]?.push(e);
      this.edgesByNodeId[e.target]?.push(e);
    });

    this.memberEdges = this.edges.filter((e) => e.rel === 'type_membership');
    this.relEdges = this.edges.filter((e) => e.rel !== 'type_membership');

    this._resizeObserver = new ResizeObserver(() => this.resize());
    this._resizeObserver.observe(canvas);
    this.resize();
    this.fit(false);
    this._setupEvents();
    this._running = true;
    this._startSimulation();
    this._loop();
  }

  destroy() {
    this._running = false;
    this._sim?.stop();
    this._resizeObserver.disconnect();
    this._cleanupEvents?.();
  }

  _startSimulation() {
    const nodes = this.nodes.map((n) => ({ ...n, _ref: n }));
    const nodeIndex = {};
    nodes.forEach((n) => (nodeIndex[n.id] = n));

    const memberLinks = this.memberEdges
      .map((e) => ({ source: nodeIndex[e.source], target: nodeIndex[e.target], isMember: true }))
      .filter((l) => l.source && l.target);

    const relLinks = this.relEdges
      .map((e) => ({ source: nodeIndex[e.source], target: nodeIndex[e.target], isMember: false }))
      .filter((l) => l.source && l.target);

    const allLinks = [...memberLinks, ...relLinks];

    this._sim = forceSimulation(nodes)
      .alpha(1)
      .alphaDecay(0.04)
      .force(
        'link',
        forceLink(allLinks)
          .id((d) => d.id)
          .distance((l) => (l.isMember ? 180 : 60))
          .strength((l) => (l.isMember ? 0.2 : 0.7)),
      )
      .force(
        'charge',
        forceManyBody()
          .strength((d) => (d.type === 'category' ? -800 : -40))
          .distanceMax(600),
      )
      .force('collide', forceCollide((d) => (d.type === 'category' ? 28 : 7)).strength(0.8))
      .on('tick', () => {
        nodes.forEach((n) => {
          n._ref.x = n.x;
          n._ref.y = n.y;
        });
        this.dirty = true;
      })
      .on('end', () => {
        if (!this._userInteracted) this.fit(true);
      });
  }

  resize() {
    const dpr = window.devicePixelRatio || 1;
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.canvas.width = w * dpr;
    this.canvas.height = h * dpr;
    this.ctx = this.canvas.getContext('2d');
    this.ctx.scale(dpr, dpr);
    this.logW = w;
    this.logH = h;
    this.dirty = true;
  }

  s2w(sx, sy) {
    return [(sx - this.tx) / this.scale, (sy - this.ty) / this.scale];
  }

  w2s(wx, wy) {
    return [wx * this.scale + this.tx, wy * this.scale + this.ty];
  }

  fit(animate = true, fromUser = false) {
    if (fromUser) this._userInteracted = false;
    const visible = this.nodes.filter((n) => this.visibleIds.has(n.id));
    if (!visible.length) return;
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
    visible.forEach((n) => {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    });
    const pad = 80,
      W = this.logW || 800,
      H = this.logH || 600;
    const gw = maxX - minX || 1,
      gh = maxY - minY || 1;
    const scale = Math.min((W - pad * 2) / gw, (H - pad * 2) / gh);
    const tx = W / 2 - (minX + gw / 2) * scale;
    const ty = H / 2 - (minY + gh / 2) * scale;
    if (animate) {
      this._animateTo(tx, ty, scale);
    } else {
      this.tx = tx;
      this.ty = ty;
      this.scale = scale;
      this._atx = tx;
      this._aty = ty;
      this._asc = scale;
    }
  }

  _animateTo(tx, ty, scale) {
    this._atx = tx;
    this._aty = ty;
    this._asc = scale;
    this._animating = true;
    this.dirty = true;
  }

  zoom(factor, cx, cy) {
    cx ??= (this.logW || 800) / 2;
    cy ??= (this.logH || 600) / 2;
    const newScale = Math.max(0.02, Math.min(12, this.scale * factor));
    const tx = cx - (cx - this.tx) * (newScale / this.scale);
    const ty = cy - (cy - this.ty) * (newScale / this.scale);
    this._animateTo(tx, ty, newScale);
  }

  centerOn(node, targetScale) {
    const W = this.logW || 800,
      H = this.logH || 600;
    const s = targetScale ?? Math.max(this.scale, 0.5);
    this._animateTo(W / 2 - node.x * s, H / 2 - node.y * s, s);
  }

  toggleEdges() {
    this.showEdges = !this.showEdges;
    this.dirty = true;
  }

  jumpRandom() {
    const pool = this.nodes.filter((n) => n.type === 'jutsu' && this.visibleIds.has(n.id));
    if (!pool.length) return;
    const node = pool[Math.floor(Math.random() * pool.length)];
    this.select(node);
    this.centerOn(node, Math.max(this.scale, 1));
  }

  _loop() {
    if (!this._running) return;

    if (this._animating) {
      const t = 0.1;
      this.tx += (this._atx - this.tx) * t;
      this.ty += (this._aty - this.ty) * t;
      this.scale += (this._asc - this.scale) * t;
      const done =
        Math.abs(this.tx - this._atx) < 0.3 &&
        Math.abs(this.ty - this._aty) < 0.3 &&
        Math.abs(this.scale - this._asc) < 0.0005;
      if (done) {
        this.tx = this._atx;
        this.ty = this._aty;
        this.scale = this._asc;
        this._animating = false;
      }
      this.dirty = true;
    }

    if (this.dirty || this.hovered) {
      this._render();
      this.dirty = false;
    }

    requestAnimationFrame(() => this._loop());
  }

  _render() {
    const { ctx, logW: W = 800, logH: H = 600 } = this;

    // Radial gradient background
    const grad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.7);
    grad.addColorStop(0, '#0f0f1e');
    grad.addColorStop(1, '#050510');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    ctx.save();
    ctx.translate(this.tx, this.ty);
    ctx.scale(this.scale, this.scale);
    if (this.showEdges) this._drawEdges();
    this._drawNodes();
    ctx.restore();

    if (this.hovered) this._drawTooltip();
  }

  _drawEdges() {
    const { ctx } = this;
    const s = this.scale;

    if (this.dimmed) {
      ctx.lineWidth = 1.2 / s;
      this.edges.forEach((e) => {
        if (!this.highlighted.has(e.source) && !this.highlighted.has(e.target)) return;
        const src = this.nodeById[e.source],
          tgt = this.nodeById[e.target];
        if (!src || !tgt) return;
        ctx.globalAlpha = e.rel === 'type_membership' ? 0.5 : 1;
        ctx.strokeStyle = e.rel === 'type_membership' ? e.color || '#666' : '#FFD700';
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();
      });
      ctx.globalAlpha = 1;
      return;
    }

    // Membership edges — batched by color
    ctx.globalAlpha = 0.18;
    ctx.lineWidth = 0.5 / s;
    const byColor = {};
    this.memberEdges.forEach((e) => {
      const src = this.nodeById[e.source],
        tgt = this.nodeById[e.target];
      if (!src || !tgt || !this.visibleIds.has(e.source) || !this.visibleIds.has(e.target)) return;
      const c = e.color || '#666';
      (byColor[c] ??= []).push([src.x, src.y, tgt.x, tgt.y]);
    });
    Object.entries(byColor).forEach(([color, segs]) => {
      ctx.strokeStyle = color;
      ctx.beginPath();
      segs.forEach(([x1, y1, x2, y2]) => {
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
      });
      ctx.stroke();
    });

    // Relationship edges — dashed gold
    if (this.relEdges.length) {
      ctx.globalAlpha = 0.5;
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 0.8 / s;
      ctx.setLineDash([5 / s, 5 / s]);
      ctx.beginPath();
      this.relEdges.forEach((e) => {
        const src = this.nodeById[e.source],
          tgt = this.nodeById[e.target];
        if (!src || !tgt || !this.visibleIds.has(e.source) || !this.visibleIds.has(e.target))
          return;
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.globalAlpha = 1;
  }

  _drawNodes() {
    const { ctx } = this;
    const s = this.scale;
    const showLabel = s > 0.08;

    // Jutsu nodes
    this.nodes.forEach((n) => {
      if (n.type !== 'jutsu' || !this.visibleIds.has(n.id)) return;
      const isDim = this.dimmed && !this.highlighted.has(n.id);
      const isSel = this.selected?.id === n.id;
      const isHov = this.hovered?.id === n.id;

      ctx.globalAlpha = isDim ? 0.03 : 1;

      const r = isSel ? 9 : isHov ? 7 : 4.5;

      if (isSel || isHov) {
        ctx.shadowColor = n.color;
        ctx.shadowBlur = isSel ? 22 : 12;
      }

      ctx.fillStyle = n.color;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();

      if (isSel) {
        ctx.shadowBlur = 0;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5 / s;
        ctx.stroke();
      } else if (isHov) {
        ctx.shadowBlur = 0;
      }

      ctx.globalAlpha = 1;
    });

    // Category (hub) nodes — always on top
    this.nodes.forEach((n) => {
      if (n.type !== 'category') return;
      const isSel = this.selected?.id === n.id;
      const isHov = this.hovered?.id === n.id;
      const r = 18;

      ctx.shadowColor = n.color;
      ctx.shadowBlur = isHov || isSel ? 35 : 20;

      ctx.fillStyle = n.color;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();

      ctx.shadowBlur = 0;
      if (isSel) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2 / s;
        ctx.stroke();
      }

      if (showLabel) {
        const fs = Math.max(8, Math.min(13, 11 / s));
        ctx.fillStyle = '#fff';
        ctx.font = `bold ${fs}px 'Segoe UI', sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(n.label, n.x, n.y);
      }
    });

    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  }

  _drawTooltip() {
    const n = this.hovered;
    if (!n || n.type === 'category') return;

    const { ctx, logW: W = 800, logH: H = 600 } = this;
    const [sx, sy] = this.w2s(n.x, n.y);

    const label = n.label;
    const fs = 12;
    ctx.font = `${fs}px 'Segoe UI', sans-serif`;
    const tw = ctx.measureText(label).width;
    const pad = 7;
    const bw = tw + pad * 2;
    const bh = 22;

    let bx = sx + 14;
    let by = sy - bh / 2;
    if (bx + bw > W - 8) bx = sx - bw - 14;
    if (by < 8) by = 8;
    if (by + bh > H - 8) by = H - bh - 8;

    ctx.fillStyle = 'rgba(5,5,20,0.92)';
    ctx.strokeStyle = n.color + 'aa';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(bx, by, bw, bh, 4);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#eee';
    ctx.font = `${fs}px 'Segoe UI', sans-serif`;
    ctx.fillText(label, bx + pad, by + bh / 2 + 4);
  }

  hitTest(sx, sy) {
    const [wx, wy] = this.s2w(sx, sy);
    let best = null,
      bestDist = Infinity;
    this.nodes.forEach((n) => {
      if (!this.visibleIds.has(n.id)) return;
      const threshold = (n.type === 'category' ? 22 : 9) / this.scale;
      const d = Math.hypot(n.x - wx, n.y - wy);
      if (d < threshold && d < bestDist) {
        bestDist = d;
        best = n;
      }
    });
    return best;
  }

  select(node) {
    this.selected = node;
    this.highlighted.clear();
    if (node) {
      this.highlighted.add(node.id);
      (this.edgesByNodeId[node.id] || []).forEach((e) => {
        this.highlighted.add(e.source);
        this.highlighted.add(e.target);
      });
      this.dimmed = true;
      this.centerOn(node, Math.max(this.scale, 0.6));
    } else {
      this.dimmed = false;
    }
    this.dirty = true;
    this.callbacks.onSelect?.(node);
  }

  setFilters({ activeTypes, activeRanks, activeChakras, searchQuery }) {
    // Copy to plain Sets to avoid Svelte reactive proxy tracking inside class methods
    this.activeTypes = new Set(activeTypes);
    this.activeRanks = new Set(activeRanks);
    this.activeChakras = new Set(activeChakras);
    this.searchQuery = searchQuery;
    this._applyFilters();
  }

  _applyFilters() {
    const { activeTypes, activeRanks, activeChakras, searchQuery } = this;
    const ft = activeTypes.size > 0,
      fr = activeRanks.size > 0;
    const fc = activeChakras.size > 0,
      fs = searchQuery.length >= 2;
    const any = ft || fr || fc || fs;

    this.visibleIds.clear();
    this.nodes.forEach((n) => {
      if (n.type === 'category') {
        this.visibleIds.add(n.id);
        return;
      }
      if (!any) {
        this.visibleIds.add(n.id);
        return;
      }
      let ok = true;
      if (ft) ok = ok && n.jutsu_types?.some((t) => activeTypes.has(t));
      if (fr) ok = ok && (n.rank ? activeRanks.has(n.rank) : activeRanks.has('None'));
      if (fc) ok = ok && n.chakra_natures?.some((c) => activeChakras.has(c));
      if (fs) ok = ok && n.label.toLowerCase().includes(searchQuery);
      if (ok) this.visibleIds.add(n.id);
    });

    this.select(null);
    if (any) {
      this._userInteracted = false;
      this.fit(true);
    }
  }

  _setupEvents() {
    const c = this.canvas;
    let drag = null;

    const onMousedown = (e) => {
      if (e.button !== 0) return;
      drag = { sx: e.clientX, sy: e.clientY, tx: this.tx, ty: this.ty, moved: false };
    };
    const onMousemove = (e) => {
      const rect = c.getBoundingClientRect();
      this.mouseX = e.clientX - rect.left;
      this.mouseY = e.clientY - rect.top;

      if (drag) {
        const dx = e.clientX - drag.sx,
          dy = e.clientY - drag.sy;
        if (!drag.moved && Math.hypot(dx, dy) > 4) drag.moved = true;
        if (drag.moved) {
          this.tx = drag.tx + dx;
          this.ty = drag.ty + dy;
          this._atx = this.tx;
          this._aty = this.ty;
          this._animating = false;
          this._userInteracted = true;
          this.dirty = true;
        }
      } else {
        const node = this.hitTest(this.mouseX, this.mouseY);
        if (node !== this.hovered) {
          this.hovered = node;
          c.style.cursor = node ? 'pointer' : 'grab';
          this.dirty = true;
        }
      }
    };
    const onMouseup = (e) => {
      if (drag && !drag.moved) {
        const rect = c.getBoundingClientRect();
        this.select(this.hitTest(e.clientX - rect.left, e.clientY - rect.top));
      }
      drag = null;
    };
    const onWheel = (e) => {
      e.preventDefault();
      const rect = c.getBoundingClientRect();
      const mx = e.clientX - rect.left,
        my = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      const newScale = Math.max(0.02, Math.min(12, this.scale * factor));
      const tx = mx - (mx - this.tx) * (newScale / this.scale);
      const ty = my - (my - this.ty) * (newScale / this.scale);
      this.tx = tx;
      this.ty = ty;
      this.scale = newScale;
      this._atx = tx;
      this._aty = ty;
      this._asc = newScale;
      this._animating = false;
      this._userInteracted = true;
      this.dirty = true;
    };
    const onMouseleave = () => {
      this.hovered = null;
      this.dirty = true;
    };

    c.addEventListener('mousedown', onMousedown);
    window.addEventListener('mousemove', onMousemove);
    window.addEventListener('mouseup', onMouseup);
    c.addEventListener('wheel', onWheel, { passive: false });
    c.addEventListener('mouseleave', onMouseleave);

    this._cleanupEvents = () => {
      c.removeEventListener('mousedown', onMousedown);
      window.removeEventListener('mousemove', onMousemove);
      window.removeEventListener('mouseup', onMouseup);
      c.removeEventListener('wheel', onWheel);
      c.removeEventListener('mouseleave', onMouseleave);
    };
  }
}
