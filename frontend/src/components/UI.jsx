import { useState } from 'react'

const uiStyles = `
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px;
    transition: border-color .2s;
  }
  .card:hover { border-color: var(--border2); }
  .card-title {
    font-family: var(--font-display); font-weight: 700; font-size: 14px;
    margin-bottom: 16px; display: flex; align-items: center; gap: 7px;
  }

  .stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px;
    position: relative; overflow: hidden;
    transition: transform .2s, border-color .2s;
  }
  .stat-card:hover { transform: translateY(-2px); border-color: var(--border2); }
  .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
  .stat-card.blue::before   { background: var(--accent);  }
  .stat-card.purple::before { background: var(--accent2); }
  .stat-card.green::before  { background: var(--green);   }
  .stat-card.orange::before { background: var(--orange);  }
  .stat-icon {
    width: 36px; height: 36px; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; margin-bottom: 12px;
  }
  .stat-icon.blue   { background: rgba(79,124,255,.12); }
  .stat-icon.purple { background: rgba(167,139,250,.12); }
  .stat-icon.green  { background: rgba(52,211,153,.12); }
  .stat-icon.orange { background: rgba(251,146,60,.12); }
  .stat-value { font-family: var(--font-display); font-weight: 800; font-size: 26px; line-height: 1; margin-bottom: 3px; }
  .stat-label { color: var(--muted); font-size: 11px; font-weight: 500; }
  .stat-delta {
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 10px; font-weight: 600; margin-top: 7px;
    padding: 2px 7px; border-radius: 99px;
  }
  .stat-delta.up   { background: rgba(52,211,153,.12); color: var(--green); }
  .stat-delta.down { background: rgba(251,146,60,.12);  color: var(--orange); }

  .tag {
    display: inline-flex; align-items: center;
    padding: 3px 9px; border-radius: 99px;
    font-size: 10px; font-weight: 600;
    background: var(--surface2); border: 1px solid var(--border); color: var(--muted);
  }
  .tag.blue   { background: rgba(79,124,255,.1);  border-color: rgba(79,124,255,.2);  color: var(--accent); }
  .tag.green  { background: rgba(52,211,153,.1);  border-color: rgba(52,211,153,.2);  color: var(--green); }
  .tag.purple { background: rgba(167,139,250,.1); border-color: rgba(167,139,250,.2); color: var(--accent2); }
  .tag.orange { background: rgba(251,146,60,.1);  border-color: rgba(251,146,60,.2);  color: var(--orange); }
  .tag.pink   { background: rgba(244,114,182,.1); border-color: rgba(244,114,182,.2); color: var(--pink); }

  .btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border-radius: var(--radius-sm);
    font-family: var(--font-body); font-size: 12px; font-weight: 600;
    cursor: pointer; border: none; transition: all .15s; white-space: nowrap;
  }
  .btn-primary   { background: var(--accent); color: #fff; }
  .btn-primary:hover { background: #3d6be8; transform: translateY(-1px); }
  .btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { border-color: var(--border2); }
  .btn-ghost     { background: transparent; color: var(--muted); }
  .btn-ghost:hover { color: var(--text); background: var(--surface2); }
  .btn-green     { background: var(--green); color: #0a0d14; }
  .btn-green:hover { opacity: .85; }
  .btn-sm        { padding: 5px 11px; font-size: 11px; }

  .progress-bar  { height: 5px; background: var(--surface2); border-radius: 99px; overflow: hidden; }
  .progress-fill { height: 100%; border-radius: 99px; transition: width .6s cubic-bezier(.4,0,.2,1); }

  .input {
    width: 100%; background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 8px 12px;
    color: var(--text); font-family: var(--font-body); font-size: 13px;
    outline: none; transition: border-color .15s;
  }
  .input:focus      { border-color: var(--accent); }
  .input::placeholder { color: var(--muted); }
  .input-group      { position: relative; }
  .input-icon       { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 13px; pointer-events: none; }
  .input-group .input { padding-left: 32px; }

  .section-header  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
  .section-title   { font-family: var(--font-display); font-weight: 700; font-size: 19px; }
  .section-sub     { color: var(--muted); font-size: 12px; margin-top: 2px; }

  .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }
  .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }
  .grid-2 { display: grid; grid-template-columns: repeat(2,1fr); gap: 14px; }
  .grid-auto { display: grid; grid-template-columns: repeat(auto-fill,minmax(270px,1fr)); gap: 14px; }

  .list-item { display: flex; align-items: center; gap: 11px; padding: 11px 0; border-bottom: 1px solid var(--border); }
  .list-item:last-child { border-bottom: none; }

  .tabs    { display: flex; gap: 2px; background: var(--surface2); padding: 3px; border-radius: var(--radius-sm); width: fit-content; }
  .tab-btn {
    padding: 6px 14px; border-radius: 5px;
    font-size: 12px; font-weight: 600; cursor: pointer;
    color: var(--muted); transition: all .15s;
    border: none; background: transparent; font-family: var(--font-body); white-space: nowrap;
  }
  .tab-btn.active { background: var(--surface); color: var(--text); }

  .skill-row  { display: flex; align-items: center; gap: 9px; margin-bottom: 10px; }
  .skill-name { width: 115px; font-size: 12px; font-weight: 500; flex-shrink: 0; }
  .dot-row    { display: flex; gap: 3px; }
  .dot        { width: 7px; height: 7px; border-radius: 50%; }
  .dot.on     { background: var(--accent); }
  .dot.off    { background: var(--surface2); border: 1px solid var(--border); }

  .welcome-banner {
    background: linear-gradient(135deg, rgba(79,124,255,.1), rgba(167,139,250,.06));
    border: 1px solid rgba(79,124,255,.18);
    border-radius: var(--radius); padding: 26px 30px;
    margin-bottom: 24px; position: relative; overflow: hidden;
  }
  .welcome-banner::before {
    content: ''; position: absolute; top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(79,124,255,.14), transparent 70%);
    pointer-events: none;
  }
  .welcome-title  { font-family: var(--font-display); font-weight: 800; font-size: 20px; margin-bottom: 5px; }
  .welcome-sub    { color: var(--muted); font-size: 13px; }
  .welcome-actions{ display: flex; gap: 9px; margin-top: 16px; }

  .kpi-ring-wrap  { display: flex; align-items: center; gap: 16px; }
  .kpi-ring       { position: relative; }
  .kpi-ring svg   { transform: rotate(-90deg); }
  .kpi-ring-label {
    position: absolute; inset: 0;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    font-family: var(--font-display);
  }
  .kpi-ring-val { font-weight: 800; font-size: 18px; }
  .kpi-ring-sub { font-size: 9px; color: var(--muted); font-weight: 500; }

  @media (max-width: 900px) {
    .grid-4 { grid-template-columns: repeat(2,1fr); }
    .grid-3 { grid-template-columns: repeat(2,1fr); }
  }
  @media (max-width: 500px) {
    .grid-4,.grid-3,.grid-2 { grid-template-columns: 1fr; }
  }
`

let stylesInjected = false
function injectStyles() {
  if (stylesInjected) return
  const el = document.createElement('style')
  el.textContent = uiStyles
  document.head.appendChild(el)
  stylesInjected = true
}

export function Card({ title, children, style }) {
  injectStyles()
  return (
    <div className="card" style={style}>
      {title && <div className="card-title">{title}</div>}
      {children}
    </div>
  )
}

export function StatCard({ icon, value, label, delta, deltaType = 'up', color = 'blue' }) {
  injectStyles()
  return (
    <div className={`stat-card ${color}`}>
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {delta && <div className={`stat-delta ${deltaType}`}>↑ {delta}</div>}
    </div>
  )
}

export function Tag({ children, color = '' }) {
  injectStyles()
  return <span className={`tag ${color}`}>{children}</span>
}

export function Btn({ children, variant = 'primary', size = '', onClick, style }) {
  injectStyles()
  return (
    <button className={`btn btn-${variant} ${size ? `btn-${size}` : ''}`} onClick={onClick} style={style}>
      {children}
    </button>
  )
}

export function ProgressBar({ value, color = 'var(--accent)', height = 5 }) {
  injectStyles()
  return (
    <div className="progress-bar" style={{ height }}>
      <div className="progress-fill" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
    </div>
  )
}

export function Input({ placeholder, value, onChange, icon, style }) {
  injectStyles()
  if (icon) return (
    <div className="input-group" style={style}>
      <span className="input-icon">{icon}</span>
      <input className="input" placeholder={placeholder} value={value} onChange={onChange} />
    </div>
  )
  return <input className="input" placeholder={placeholder} value={value} onChange={onChange} style={style} />
}

export function Tabs({ items, active, onChange }) {
  injectStyles()
  return (
    <div className="tabs">
      {items.map(t => (
        <button key={t} className={`tab-btn ${active === t ? 'active' : ''}`} onClick={() => onChange(t)}>
          {t.charAt(0).toUpperCase() + t.slice(1)}
        </button>
      ))}
    </div>
  )
}

export function SkillDots({ level }) {
  injectStyles()
  const scores = { débutant: 1, intermédiaire: 2, avancé: 3, expert: 4 }
  const filled = scores[level] || 1
  return (
    <div className="dot-row">
      {[1,2,3,4].map(i => <div key={i} className={`dot ${i <= filled ? 'on' : 'off'}`} />)}
    </div>
  )
}

export function RingChart({ value, color = 'var(--accent)', size = 80 }) {
  injectStyles()
  const r = 34, cx = size / 2, cy = size / 2
  const circ  = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  return (
    <div className="kpi-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth="7" />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="7"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="kpi-ring-label">
        <span className="kpi-ring-val">{value}%</span>
      </div>
    </div>
  )
}

export function Avatar({ initials, color = '#4f7cff', size = 36 }) {
  injectStyles()
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: `${color}22`, color,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 700, fontSize: size * 0.35, flexShrink: 0,
    }}>
      {initials}
    </div>
  )
}

export function SectionHeader({ title, sub, action }) {
  injectStyles()
  return (
    <div className="section-header">
      <div>
        <div className="section-title">{title}</div>
        {sub && <div className="section-sub">{sub}</div>}
      </div>
      {action}
    </div>
  )
}