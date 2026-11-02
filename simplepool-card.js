/*
 * SimplePool Card
 * Carte Lovelace livrée avec l'intégration simplepool.
 * Aucune dépendance (ni button-card, ni mushroom, ni card-mod).
 */
const CARD_VERSION = "0.1.1";

const DEFAULT_ENTITIES = {
  prog: "switch.piscine_programmation",
  hg: "switch.piscine_hors_gel",
  boost: "switch.piscine_boost",
  p1d: "select.piscine_plage_1_debut",
  p1l: "select.piscine_plage_1_duree",
  p2d: "select.piscine_plage_2_debut",
  p2l: "select.piscine_plage_2_duree",
  vol: "number.piscine_volume",
  deb: "number.piscine_debit_pompe",
  bdur: "number.piscine_boost_duree",
  seuil: "number.piscine_seuil_hors_gel",
  cons: "sensor.piscine_duree_conseillee",
  turn: "sensor.piscine_turnover",
  gel: "binary_sensor.piscine_gel_detecte",
  plan: "binary_sensor.piscine_pompe_planifiee",
};

const C = {
  bg: "#0a0f1d", s1: "#70e000", s2: "#2ec4b6", both: "#ffd166", off: "#1c2336",
  red: "#ff6b6b", ice: "#90e0ef", blue: "#3a86ff", label: "#8ecae6",
};

const parseHM = (v) => {
  const p = String(v ?? "").split("h");
  return p.length === 2 ? (parseInt(p[0], 10) || 0) + (parseInt(p[1], 10) || 0) / 60 : 0;
};
const fmtH = (x) => {
  x = ((x % 24) + 24) % 24;
  let H = Math.floor(x), M = Math.round((x - H) * 60);
  if (M === 60) { H = (H + 1) % 24; M = 0; }
  return `${String(H).padStart(2, "0")}h${String(M).padStart(2, "0")}`;
};
const fmtDur = (x) => {
  const H = Math.floor(x), M = Math.round((x - H) * 60);
  return `${H}h${String(M).padStart(2, "0")}`;
};
const inSlot = (x, s, d) => d > 0 && (((x - s) % 24) + 24) % 24 < d;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

class SimplePoolCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._last = null;
    this._bound = false;
  }

  static getStubConfig() { return {}; }
  getCardSize() { return 14; }

  setConfig(config) {
    this._config = config || {};
    this._e = { ...DEFAULT_ENTITIES, ...(this._config.entities || {}) };
    this._resolved = false;
    this._last = null;
    this._maybeRender();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._resolved) this._resolve();
    this._maybeRender();
  }

  connectedCallback() {
    this._timer = setInterval(() => this._maybeRender(), 15000);
    this._maybeRender();
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  /* Retrouve les entités de l'intégration quel que soit leur identifiant :
     Home Assistant peut y insérer le nom de l'appareil (ex. piscine_nonopool_volume)
     ou ajouter un suffixe (_2) si d'anciennes entités du même nom existent. */
  _resolve() {
    const states = this._hass?.states;
    if (!states) return;
    const custom = this._config.entities || {};
    const reg = this._hass.entities || {};
    const ids = Object.keys(states);
    let all = true;
    for (const [key, def] of Object.entries(DEFAULT_ENTITIES)) {
      if (custom[key]) continue;
      const [domain, objectId] = def.split(".");
      const suffix = objectId.replace(/^piscine_/, "");
      const re = new RegExp(`^${domain}\\.(?:.+_)?${suffix}(?:_\\d+)?$`);
      const ours = ids
        .filter((id) => re.test(id) && reg[id]?.platform === "simplepool")
        .sort((a, b) => a.length - b.length);
      const found = ours[0] || (states[def] ? def : undefined);
      if (found) this._e[key] = found; else all = false;
    }
    this._resolved = all;
  }

  /* ------------------------------------------------------------- helpers */
  _st(id) { return id ? this._hass?.states?.[id] : undefined; }
  _on(id) { return this._st(id)?.state === "on"; }
  _num(id) { const v = parseFloat(this._st(id)?.state); return isNaN(v) ? null : v; }

  _ext() {
    const a = this._st(this._e.plan)?.attributes || {};
    return {
      pump: this._config.pump_entity || a.pump_entity,
      water: this._config.water_temp_entity || a.water_temp_entity,
      air: this._config.air_temp_entity || a.air_temp_entity,
    };
  }

  _clock(date = new Date()) {
    try {
      const parts = new Intl.DateTimeFormat("fr-FR", {
        timeZone: this._hass?.config?.time_zone, hour: "2-digit", minute: "2-digit", hourCycle: "h23",
      }).formatToParts(date);
      const h = parseInt(parts.find((p) => p.type === "hour").value, 10) % 24;
      const m = parseInt(parts.find((p) => p.type === "minute").value, 10);
      return h + m / 60;
    } catch (e) {
      return date.getHours() + date.getMinutes() / 60;
    }
  }

  _signature() {
    const x = this._ext();
    const ids = [...Object.values(this._e), x.pump, x.water, x.air];
    return ids.map((id) => {
      const s = this._st(id);
      return s ? `${s.state}|${s.attributes.fin ?? ""}` : "-";
    }).join(";") + "@" + Math.floor(this._clock() * 60);
  }

  _maybeRender() {
    if (!this._hass || !this._config || !this.shadowRoot) return;
    const active = this.shadowRoot.activeElement;
    if (active && active.tagName === "INPUT") return; // ne pas écraser une saisie
    const sig = this._signature();
    if (sig === this._last) return;
    this._last = sig;
    this._render();
  }

  _call(domain, service, data) { this._hass.callService(domain, service, data); }

  _moreInfo(entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  _setNumber(id, value) {
    const s = this._st(id);
    if (!s) return;
    const min = parseFloat(s.attributes.min), max = parseFloat(s.attributes.max);
    const step = parseFloat(s.attributes.step) || 1;
    let v = Math.min(max, Math.max(min, value));
    v = Math.round((v - min) / step) * step + min;
    this._call("number", "set_value", { entity_id: id, value: Number(v.toFixed(3)) });
  }

  _bind() {
    if (this._bound) return;
    this._bound = true;
    const root = this.shadowRoot;
    root.addEventListener("click", (ev) => {
      const t = ev.target.closest("[data-action]");
      if (!t) return;
      const id = t.dataset.entity;
      switch (t.dataset.action) {
        case "toggle": this._call("switch", "toggle", { entity_id: id }); break;
        case "more": if (id) this._moreInfo(id); break;
        case "step": {
          const cur = this._num(id);
          const step = parseFloat(this._st(id)?.attributes.step) || 1;
          if (cur !== null) this._setNumber(id, cur + step * parseFloat(t.dataset.dir));
          break;
        }
      }
    });
    root.addEventListener("change", (ev) => {
      const t = ev.target;
      if (t.dataset.select) {
        this._call("select", "select_option", { entity_id: t.dataset.select, option: t.value });
      } else if (t.dataset.number) {
        const v = parseFloat(String(t.value).replace(",", "."));
        if (!isNaN(v)) this._setNumber(t.dataset.number, v);
        t.blur();
      }
    });
    root.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && ev.target.tagName === "INPUT") ev.target.blur();
    });
    root.addEventListener("focusout", (ev) => {
      if (ev.target.tagName === "INPUT") setTimeout(() => { this._last = null; this._maybeRender(); }, 250);
    });
  }

  /* --------------------------------------------------------------- rendu */
  _dial(d) {
    const cx = 150, cy = 150;
    const pol = (r, a) => { const k = ((a - 90) * Math.PI) / 180; return [cx + r * Math.cos(k), cy + r * Math.sin(k)]; };
    const ang = (x) => (((x % 24) + 24) % 24) * 15;
    let svg = "";
    for (let i = 0; i < 96; i++) {
      const x = i / 4 + 0.125, a = inSlot(x, d.s1, d.d1), b = inSlot(x, d.s2, d.d2);
      const col = a && b ? C.both : a ? C.s1 : b ? C.s2 : C.off;
      const [x1, y1] = pol(118, ang(x)), [x2, y2] = pol(138, ang(x));
      svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="5" stroke-linecap="round" opacity="${col !== C.off && !d.prog ? 0.3 : 1}"/>`;
    }
    for (let i = 0; i < 24; i++) {
      const M = i % 6 === 0;
      const [tx1, ty1] = pol(108, ang(i)), [tx2, ty2] = pol(112, ang(i));
      svg += `<line x1="${tx1}" y1="${ty1}" x2="${tx2}" y2="${ty2}" stroke="rgba(255,255,255,${M ? 0.6 : 0.2})" stroke-width="${M ? 2 : 1}"/>`;
      const [lx, ly] = pol(96, ang(i));
      svg += `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" font-size="${M ? 13 : 9}" font-weight="${M ? 700 : 400}" fill="${M ? C.label : "rgba(255,255,255,0.45)"}">${i}</text>`;
    }
    const [nx1, ny1] = pol(76, ang(d.h)), [nx2, ny2] = pol(144, ang(d.h));
    svg += `<line x1="${nx1}" y1="${ny1}" x2="${nx2}" y2="${ny2}" stroke="${C.red}" stroke-width="3" stroke-linecap="round"/><circle cx="${nx2}" cy="${ny2}" r="5" fill="${C.red}"/>`;
    const ring = d.boost ? C.red : d.gel ? C.ice : d.running ? C.s1 : "rgba(255,255,255,0.06)";
    svg += `<circle cx="${cx}" cy="${cy}" r="72" fill="${C.bg}" stroke="${ring}" stroke-width="${d.running || d.boost || d.gel ? 2 : 1}"/>`;
    svg += `<text x="${cx}" y="${cy + 2}" text-anchor="middle" font-size="38" font-weight="700" fill="#fff">${fmtH(d.h)}</text>`;
    svg += `<text x="${cx}" y="${cy + 26}" text-anchor="middle" font-size="11" fill="${d.statusColor}">${esc(d.status)}</text>`;
    return `<svg viewBox="0 0 300 300" class="dial">${svg}</svg>`;
  }

  _mode(id, name, icon, color, sub) {
    const on = this._on(id);
    return `<div class="mode ${on ? "on" : ""}" style="--c:${color}" data-action="toggle" data-entity="${id}">
      <ha-icon icon="${icon}"></ha-icon><div class="mname">${name}</div><div class="msub">${esc(sub)}</div></div>`;
  }

  _select(id, label, icon, color) {
    const s = this._st(id);
    const opts = (s?.attributes.options || []).map((o) => `<option value="${esc(o)}" ${o === s.state ? "selected" : ""}>${esc(o)}</option>`).join("");
    return `<label class="tile"><span class="tlabel"><ha-icon icon="${icon}" style="color:${color}"></ha-icon>${label}</span>
      <select data-select="${id}">${opts}</select></label>`;
  }

  _number(id, label, icon) {
    const s = this._st(id);
    const v = this._num(id);
    const unit = s?.attributes.unit_of_measurement || "";
    return `<div class="tile">
      <span class="tlabel" data-action="more" data-entity="${id}"><ha-icon icon="${icon}" style="color:${C.label}"></ha-icon>${label}</span>
      <div class="stepper">
        <button data-action="step" data-dir="-1" data-entity="${id}" aria-label="Moins">−</button>
        <input type="number" inputmode="decimal" data-number="${id}" value="${v ?? ""}"
          min="${s?.attributes.min ?? ""}" max="${s?.attributes.max ?? ""}" step="${s?.attributes.step ?? ""}">
        <span class="unit">${esc(unit)}</span>
        <button data-action="step" data-dir="1" data-entity="${id}" aria-label="Plus">+</button>
      </div></div>`;
  }

  _plageTitle(n, color, rgba, s, d, prog) {
    const range = d > 0 ? `${fmtH(s)} → ${fmtH(s + d)}` : "Désactivée";
    return `<div class="ptitle" style="opacity:${prog ? 1 : 0.5}">
      <span><i style="background:${color}"></i>Plage ${n}</span>
      <span class="range" style="color:${color};background:${rgba}">${range}</span></div>`;
  }

  _render() {
    this._bind();
    const e = this._e;
    if (!this._st(e.plan)) {
      this._resolve();
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px;line-height:1.5">Intégration <b>SimplePool</b> introuvable :
        l'entité <code>${esc(e.plan)}</code> n'existe pas.<br>Vérifiez que l'intégration est chargée
        (Paramètres → Appareils et services) et que ses entités ne sont pas désactivées.</div></ha-card>`;
      return;
    }
    const x = this._ext();
    const pumpState = this._st(x.pump)?.state;
    const pumpOk = pumpState === "on" || pumpState === "off";
    const d = {
      s1: parseHM(this._st(e.p1d)?.state), d1: parseHM(this._st(e.p1l)?.state),
      s2: parseHM(this._st(e.p2d)?.state), d2: parseHM(this._st(e.p2l)?.state),
      prog: this._on(e.prog), boost: this._on(e.boost), hg: this._on(e.hg), gel: this._on(e.gel),
      running: pumpState === "on", h: this._clock(),
    };
    const air = this._num(x.air);
    const airTxt = air === null ? "–" : air.toFixed(1);

    // Statut au centre du cadran
    let status, sc = C.label;
    if (!pumpOk) { status = "⚠ Pompe indisponible"; sc = C.red; }
    else if (d.boost) { status = "Boost en cours"; sc = C.red; }
    else if (d.gel) { status = `❄ Hors gel actif · air ${airTxt} °C`; sc = C.ice; }
    else if (d.hg) { status = `❄ Hors gel en veille · air ${airTxt} °C`; sc = C.ice; }
    else if (!d.prog) { status = "Programmation arrêtée"; sc = "rgba(255,255,255,0.4)"; }
    else if (inSlot(d.h, d.s1, d.d1)) { status = `Filtration · fin ${fmtH(d.s1 + d.d1)}`; sc = C.s1; }
    else if (inSlot(d.h, d.s2, d.d2)) { status = `Filtration · fin ${fmtH(d.s2 + d.d2)}`; sc = C.s2; }
    else {
      const n = [[d.s1, d.d1], [d.s2, d.d2]].filter((v) => v[1] > 0)
        .map((v) => ({ s: v[0], dt: (((v[0] - d.h) % 24) + 24) % 24 })).sort((a, b) => a.dt - b.dt)[0];
      status = n ? `Prochain départ ${fmtH(n.s)}` : "Aucune plage";
    }
    d.status = status; d.statusColor = sc;

    // Indicateurs
    let q = 0;
    for (let i = 0; i < 96; i++) { const t = i / 4 + 0.125; if (inSlot(t, d.s1, d.d1) || inSlot(t, d.s2, d.d2)) q++; }
    const hrs = q / 4;
    const eau = this._num(x.water);
    const cons = this._num(e.cons);
    const turn = this._num(e.turn);
    const eauCol = eau === null ? "rgba(255,255,255,0.4)" : eau < 12 ? C.ice : eau < 24 ? C.s2 : eau < 28 ? C.both : C.red;
    const filCol = cons === null ? C.label : hrs >= cons ? C.s1 : hrs >= cons * 0.75 ? C.both : C.red;
    const toCol = turn === null ? "rgba(255,255,255,0.4)" : turn >= 100 ? C.s1 : turn >= 75 ? C.both : C.red;
    const stat = (icon, val, lbl, col, sub = "") => `<div class="stat"><ha-icon icon="${icon}" style="color:${col}"></ha-icon>
      <b>${val}</b><span>${lbl}</span>${sub ? `<small style="color:${col}">${sub}</small>` : ""}</div>`;

    // Sous-titres des modes
    const hgSub = !d.hg ? "Désactivé" : air === null ? "⚠ Pas de sonde" : `${d.gel ? "❄ Actif" : "Veille"} · ${airTxt} °C`;
    const bAttr = this._st(e.boost)?.attributes || {};
    let boostSub;
    if (d.boost && bAttr.fin) boostSub = `Jusqu’à ${fmtH(this._clock(new Date(bAttr.fin)))}`;
    else boostSub = `Marche forcée ${fmtDur(this._num(e.bdur) ?? 4)}`;

    const pill = pumpState === "on" ? [C.s1, "rgba(112,224,0,0.12)", "Pompe en marche"]
      : pumpState === "off" ? ["rgba(255,255,255,0.55)", "rgba(255,255,255,0.06)", "Pompe arrêtée"]
      : [C.red, "rgba(255,107,107,0.12)", "Pompe indisponible"];

    this.shadowRoot.innerHTML = `
      <style>${SimplePoolCard.styles}</style>
      <ha-card>
        <div class="header">
          <div class="title"><ha-icon icon="mdi:pool"></ha-icon>${esc(this._config.title ?? "Filtration piscine")}</div>
          <div class="pill" style="color:${pill[0]};background:${pill[1]}" data-action="more" data-entity="${x.pump ?? ""}">
            <i style="background:${pill[0]}"></i>${pill[2]}</div>
        </div>
        ${this._dial(d)}
        <div class="stats">
          ${stat("mdi:pool-thermometer", eau === null ? "–" : `${eau.toFixed(1)} °C`, "Eau", eauCol)}
          ${stat("mdi:timer-sand", fmtDur(hrs), "Filtration / jour", filCol, cons === null ? "" : `Conseillé ${fmtDur(cons)}`)}
          ${stat("mdi:water-sync", turn === null ? "–" : `${turn} %`, "Turnover", toCol)}
        </div>
        <div class="modes">
          ${this._mode(e.prog, "Programmation", "mdi:calendar-clock", C.blue, d.prog ? "Active" : "Arrêtée")}
          ${this._mode(e.hg, "Hors gel", "mdi:snowflake-thermometer", C.ice, hgSub)}
          ${this._mode(e.boost, "Boost", "mdi:rocket-launch", C.red, boostSub)}
        </div>
        ${this._plageTitle(1, C.s1, "rgba(112,224,0,0.12)", d.s1, d.d1, d.prog)}
        <div class="grid2">
          ${this._select(e.p1d, "Début", "mdi:clock-start", C.s1)}
          ${this._select(e.p1l, "Durée", "mdi:timer-outline", C.s1)}
        </div>
        ${this._plageTitle(2, C.s2, "rgba(46,196,182,0.12)", d.s2, d.d2, d.prog)}
        <div class="grid2">
          ${this._select(e.p2d, "Début", "mdi:clock-start", C.s2)}
          ${this._select(e.p2l, "Durée", "mdi:timer-outline", C.s2)}
        </div>
        <div class="ptitle"><span><ha-icon icon="mdi:tune-variant" style="color:${C.label};--mdc-icon-size:18px"></ha-icon>Bassin &amp; pompe</span></div>
        <div class="grid2">
          ${this._number(e.vol, "Volume", "mdi:pool")}
          ${this._number(e.deb, "Débit", "mdi:pump")}
          ${this._number(e.bdur, "Durée Boost", "mdi:rocket-launch")}
          ${this._number(e.seuil, "Seuil hors gel", "mdi:snowflake-thermometer")}
        </div>
      </ha-card>`;
  }

  static get styles() {
    return `
      ha-card { background:${C.bg}; border-radius:24px; border:1px solid rgba(255,255,255,0.05);
        padding:16px; color:#fff; max-width:460px; margin:0 auto; box-sizing:border-box; }
      .header { display:flex; justify-content:space-between; align-items:center; gap:8px; }
      .title { display:flex; align-items:center; gap:10px; font-size:18px; font-weight:600; }
      .title ha-icon { color:${C.s2}; --mdc-icon-size:26px; }
      .pill { display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:14px;
        font-size:12px; font-weight:600; cursor:pointer; white-space:nowrap; }
      .pill i, .ptitle i { width:8px; height:8px; border-radius:50%; display:inline-block; }
      .ptitle i { width:10px; height:10px; }
      .dial { width:100%; max-width:320px; display:block; margin:8px auto; }
      .stats, .modes { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:8px; }
      .stat { display:flex; flex-direction:column; align-items:center; gap:2px; padding:10px 4px;
        border-radius:16px; background:rgba(255,255,255,0.04); text-align:center; }
      .stat ha-icon { --mdc-icon-size:18px; }
      .stat b { font-size:16px; }
      .stat span { font-size:11px; color:rgba(255,255,255,0.5); }
      .stat small { font-size:10px; }
      .mode { display:flex; flex-direction:column; align-items:center; padding:14px 6px 12px; border-radius:18px;
        background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06); cursor:pointer;
        transition:all .2s; text-align:center; user-select:none; }
      .mode ha-icon { --mdc-icon-size:28px; color:rgba(255,255,255,0.35); }
      .mode.on { border-color:var(--c); background:color-mix(in srgb, var(--c) 14%, transparent); }
      .mode.on ha-icon, .mode.on .msub { color:var(--c); }
      .mname { font-size:13px; font-weight:600; margin-top:6px; }
      .msub { font-size:11px; color:rgba(255,255,255,0.5); margin-top:2px; }
      .ptitle { display:flex; justify-content:space-between; align-items:center; margin:16px 4px 8px;
        font-size:14px; font-weight:600; }
      .ptitle > span:first-child { display:flex; align-items:center; gap:8px; }
      .range { font-size:12px; padding:4px 10px; border-radius:12px; }
      .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
      .tile { display:flex; flex-direction:column; gap:8px; padding:10px 12px; border-radius:18px;
        background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06); }
      .tlabel { display:flex; align-items:center; gap:6px; font-size:12px; color:rgba(255,255,255,0.7); cursor:pointer; }
      .tlabel ha-icon { --mdc-icon-size:18px; }
      select, input { background:rgba(255,255,255,0.07); color:#fff; border:1px solid rgba(255,255,255,0.1);
        border-radius:10px; font-size:15px; font-weight:600; padding:6px 8px; font-family:inherit; }
      select { width:100%; cursor:pointer; }
      select option { background:${C.bg}; }
      .stepper { display:flex; align-items:center; gap:4px; }
      .stepper input { width:100%; min-width:0; text-align:center; -moz-appearance:textfield; padding:6px 2px; }
      .stepper input::-webkit-outer-spin-button, .stepper input::-webkit-inner-spin-button { -webkit-appearance:none; margin:0; }
      .unit { font-size:11px; color:rgba(255,255,255,0.5); white-space:nowrap; }
      .stepper button { flex:0 0 30px; height:30px; border-radius:50%; border:none; cursor:pointer;
        background:rgba(255,255,255,0.08); color:${C.label}; font-size:18px; line-height:1; }
      .stepper button:active { background:rgba(255,255,255,0.18); }
    `;
  }
}

if (!customElements.get("simplepool-card")) {
  customElements.define("simplepool-card", SimplePoolCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "simplepool-card",
    name: "SimplePool",
    description: "Programmateur 24 h, modes et réglages de la filtration de piscine.",
    preview: true,
  });
  console.info(`%c SIMPLEPOOL-CARD %c v${CARD_VERSION} `, "background:#2ec4b6;color:#000", "background:#0a0f1d;color:#fff");
}
