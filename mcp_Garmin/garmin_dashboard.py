# /// script
# requires-python = ">=3.11"
# dependencies = ["garminconnect>=0.3.20"]
# ///
"""Build a self-contained local HTML dashboard from Garmin Connect.

Standalone:  uv run ~/garmin-mcp/garmin_dashboard.py [days]
From Claude: the build_dashboard tool of the MCP server.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from garmin_common import (
    activity_row, cached_day, day_summary, drange, get_client, hrv_summary,
    parallel, readiness_summary, sleep_summary, training_load_series,
)

OUT = Path(os.path.expanduser(os.getenv("GARMIN_DASHBOARD", str(Path(__file__).with_name("dashboard.html")))))


def collect(api: Any, days: int = 30) -> dict[str, Any]:
    end = date.today()
    dates = drange(end - timedelta(days=days - 1), end)

    def one(d: date) -> dict[str, Any]:
        s = sleep_summary(cached_day("sleep", d, api.get_sleep_data) or {})
        h = hrv_summary(cached_day("hrv", d, api.get_hrv_data))
        u = day_summary(cached_day("summary", d, api.get_user_summary) or {})
        return {
            "date": d.isoformat(),
            "sleep_score": s.get("sleep_score"), "sleep_h": s.get("total_h"),
            "deep_h": s.get("deep_h"), "light_h": s.get("light_h"), "rem_h": s.get("rem_h"), "awake_h": s.get("awake_h"),
            "hrv": h.get("last_night_avg"), "hrv_7d": h.get("weekly_avg"),
            "hrv_lo": h.get("baseline_low"), "hrv_hi": h.get("baseline_high"), "hrv_status": h.get("status"),
            "rhr": u.get("resting_hr") or s.get("resting_hr"),
            "bb_high": u.get("body_battery_high"), "bb_low": u.get("body_battery_low"), "bb_now": u.get("body_battery_now"),
            "stress": u.get("avg_stress"), "steps": u.get("steps"),
        }

    rows = parallel(one, dates)
    try:
        load = training_load_series(api, days=days)["series"]
    except Exception:  # noqa: BLE001
        load = []
    try:
        acts = [activity_row(a) for a in (api.get_activities_by_date((end - timedelta(days=days)).isoformat(), end.isoformat()) or [])]
    except Exception:  # noqa: BLE001
        acts = []
    try:
        ready = readiness_summary(api.get_training_readiness(end.isoformat()))
    except Exception:  # noqa: BLE001
        ready = {}
    return {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "days": rows, "load": load,
            "activities": acts, "readiness": ready}


def render(data: dict[str, Any]) -> str:
    return TEMPLATE.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/"))


def build(api: Any, days: int = 30) -> Path:
    html = render(collect(api, days))
    OUT.write_text(html, encoding="utf-8")
    return OUT


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Garmin — восстановление и нагрузка</title>
<style>
.viz-root{color-scheme:light;--surface-0:#f6f6f4;--surface-1:#ffffff;--text-primary:#191919;--text-secondary:#666666;
 --grid:#e6e6e6;--axis:#bdbdbd;--band:#e9eef6;--s1:#257de0;--s2:#f47230;--pos:#257de0;--neg:#ec4647;
 --good:#0aac23;--warn:#fbb315;--crit:#dc3c3d}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface-0:#111111;--surface-1:#191919;
 --text-primary:#efefef;--text-secondary:#9c9c9c;--grid:#2c2c2c;--axis:#4a4a4a;--band:#1f2a3a;--s1:#338ced;--s2:#e76624;--pos:#338ced;--neg:#eb6263}}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.viz-root{background:var(--surface-0);color:var(--text-primary);min-height:100vh;padding:24px}
header{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:16px}
h1{font-size:20px;margin:0}
.muted{color:var(--text-secondary);font-size:12px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--surface-1);border-radius:12px;padding:14px 16px}
.tile .label{color:var(--text-secondary);font-size:12px}
.tile .val{font-size:28px;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums}
.tile .sub{color:var(--text-secondary);font-size:12px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:12px}
.card{background:var(--surface-1);border-radius:12px;padding:14px 16px 8px;position:relative}
.card h2{font-size:14px;margin:0 0 2px;font-weight:600}
.card .note{color:var(--text-secondary);font-size:12px;margin-bottom:6px}
.legend{display:flex;gap:14px;font-size:12px;color:var(--text-secondary);margin-bottom:4px}
.legend i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:5px}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{fill:var(--text-secondary);font-size:10px}
.tip{position:fixed;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--grid);
 border-radius:8px;padding:8px 10px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.12);display:none;z-index:9;white-space:nowrap}
.tip b{font-weight:600}
section{margin-top:16px}
table{width:100%;border-collapse:collapse;background:var(--surface-1);border-radius:12px;overflow:hidden;font-size:12.5px}
th,td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--grid);font-variant-numeric:tabular-nums}
th{color:var(--text-secondary);font-weight:500}
th:first-child,td:first-child,td.l,th.l{text-align:left}
details summary{cursor:pointer;color:var(--text-secondary);margin:8px 0}
</style></head>
<body><div class="viz-root">
<header><h1>Garmin — восстановление и нагрузка</h1><span class="muted" id="gen"></span></header>
<div class="tiles" id="tiles"></div>
<div class="grid">
 <div class="card"><h2>Сон, часы</h2><div class="note">Наведите на столбец — фазы сна и sleep score</div><div id="c_sleep"></div></div>
 <div class="card"><h2>Sleep score</h2><div class="note">0–100</div><div id="c_score"></div></div>
 <div class="card"><h2>HRV за ночь, мс</h2><div class="note">Серая полоса — ваш сбалансированный диапазон</div><div id="c_hrv"></div></div>
 <div class="card"><h2>Пульс покоя, уд/мин</h2><div class="note">Рост на 3–5 уд. — признак недовосстановления</div><div id="c_rhr"></div></div>
 <div class="card"><h2>Body Battery</h2><div class="note">Диапазон за день: минимум → максимум</div><div id="c_bb"></div></div>
 <div class="card"><h2>Средний стресс</h2><div class="note">0–100</div><div id="c_stress"></div></div>
 <div class="card"><h2>Шаги</h2><div class="note">&nbsp;</div><div id="c_steps"></div></div>
 <div class="card"><h2>Форма и усталость</h2><div class="legend"><span><i style="background:var(--s1)"></i>Fitness (CTL, 42 дня)</span><span><i style="background:var(--s2)"></i>Fatigue (ATL, 7 дней)</span></div><div id="c_load"></div></div>
 <div class="card"><h2>Form (TSB = CTL − ATL)</h2><div class="note">Ниже −20 — сильная усталость; −10…+5 — рабочая зона; выше +15 — свежесть</div><div id="c_tsb"></div></div>
</div>
<section><h2 style="font-size:15px">Тренировки</h2><table id="t_act"></table></section>
<section><details><summary>Таблица по дням</summary><table id="t_days"></table></details></section>
<div class="tip" id="tip"></div>
</div>
<script>
const DATA = /*__DATA__*/null;
const $ = s => document.querySelector(s);
const tip = $('#tip');
const fmtD = s => { const d = new Date(s+'T00:00'); return d.toLocaleDateString('ru-RU',{day:'numeric',month:'short'}); };
const num = (v,d=0) => v==null||isNaN(v) ? '—' : Number(v).toLocaleString('ru-RU',{maximumFractionDigits:d,minimumFractionDigits:d});
$('#gen').textContent = 'обновлено ' + DATA.generated;

function showTip(e, html){ tip.innerHTML = html; tip.style.display='block';
  const x = Math.min(e.clientX+14, innerWidth - tip.offsetWidth - 8), y = Math.max(8, e.clientY - tip.offsetHeight - 10);
  tip.style.left = x+'px'; tip.style.top = y+'px'; }
function hideTip(){ tip.style.display='none'; }

/* Generic small chart. opts: rows, x, kind: line|bar|range|div, series:[{key,color}], lo/hi keys for range,
   band:{lo,hi}, yMin, yMax, tip(row) */
function chart(el, o){
  const W=440, H=170, m={l:34,r:10,t:10,b:22}, iw=W-m.l-m.r, ih=H-m.t-m.b, rows=o.rows, n=rows.length;
  const vals=[]; rows.forEach(r=>{ (o.series||[]).forEach(s=>{ if(r[s.key]!=null) vals.push(r[s.key]); });
    if(o.lo&&r[o.lo]!=null) vals.push(r[o.lo]); if(o.hi&&r[o.hi]!=null) vals.push(r[o.hi]);
    if(o.band){ if(r[o.band.lo]!=null) vals.push(r[o.band.lo]); if(r[o.band.hi]!=null) vals.push(r[o.band.hi]); } });
  if(!vals.length){ el.innerHTML='<div class="muted" style="padding:40px 0;text-align:center">Нет данных</div>'; return; }
  let y0 = o.yMin!=null ? o.yMin : Math.min(...vals), y1 = o.yMax!=null ? o.yMax : Math.max(...vals);
  if(o.kind==='div'){ const a=Math.max(Math.abs(y0),Math.abs(y1),5); y0=-a; y1=a; }
  if(o.kind!=='div' && o.yMin==null){ const pad=(y1-y0)*0.15||1; y0=Math.max(o.floor??-Infinity, y0-pad); y1=y1+pad; }
  if(y1===y0) y1=y0+1;
  const step=iw/n, X=i=>m.l+step*i+step/2, Y=v=>m.t+ih-(v-y0)/(y1-y0)*ih;
  const ticks=niceTicks(y0,y1,4);
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img">`;
  ticks.forEach(t=>{ s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(t)}" y2="${Y(t)}" stroke="var(--grid)" stroke-width="1"/>`+
    `<text x="${m.l-6}" y="${Y(t)+3}" text-anchor="end">${num(t, Math.abs(t)<10 && t%1 ? 1:0)}</text>`; });
  const every=Math.ceil(n/7); rows.forEach((r,i)=>{ if(i%every===0||i===n-1) s+=`<text x="${X(i)}" y="${H-6}" text-anchor="middle">${fmtD(r.date)}</text>`; });
  if(o.band){ let p=''; let started=false; const pts=rows.map((r,i)=>[i,r[o.band.lo],r[o.band.hi]]).filter(p=>p[1]!=null&&p[2]!=null);
    if(pts.length){ p='M'+pts.map(q=>`${X(q[0])},${Y(q[2])}`).join('L')+'L'+pts.slice().reverse().map(q=>`${X(q[0])},${Y(q[1])}`).join('L')+'Z';
      s+=`<path d="${p}" fill="var(--band)" stroke="none"/>`; } }
  const bw=Math.max(2,Math.min(14,step-2)), r4=Math.min(4,bw/2);
  if(o.kind==='bar'){ const c=o.series[0].color; rows.forEach((r,i)=>{ const v=r[o.series[0].key]; if(v==null) return;
      const top=Y(v), base=Y(Math.max(y0,0)); s+=barPath(X(i)-bw/2, top, bw, base-top, r4, c, 'up'); }); }
  if(o.kind==='div'){ const k=o.series[0].key, z=Y(0); s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${z}" y2="${z}" stroke="var(--axis)"/>`;
    rows.forEach((r,i)=>{ const v=r[k]; if(v==null||v===0) return; const yv=Y(v);
      s+= v>0 ? barPath(X(i)-bw/2, yv, bw, z-yv-1, r4, 'var(--pos)','up') : barPath(X(i)-bw/2, z+1, bw, yv-z-1, r4, 'var(--neg)','down'); }); }
  if(o.kind==='range'){ rows.forEach((r,i)=>{ const a=r[o.lo], b=r[o.hi]; if(a==null||b==null) return;
      s+=`<rect x="${X(i)-bw/2}" y="${Y(b)}" width="${bw}" height="${Math.max(2,Y(a)-Y(b))}" rx="${r4}" fill="${o.series[0].color}"/>`; }); }
  if(o.kind==='line'){ o.series.forEach(se=>{ let d='', pen=false; rows.forEach((r,i)=>{ const v=r[se.key];
      if(v==null){ pen=false; return; } d+=(pen?'L':'M')+X(i)+','+Y(v); pen=true; });
      s+=`<path d="${d}" fill="none" stroke="${se.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
      if(n<=45) rows.forEach((r,i)=>{ if(r[se.key]!=null) s+=`<circle cx="${X(i)}" cy="${Y(r[se.key])}" r="2.5" fill="${se.color}" stroke="var(--surface-1)" stroke-width="1.5"/>`; }); });
    if(o.series.length>1){ const last=rows[n-1]; o.series.forEach(se=>{ if(last[se.key]!=null) s+=`<text x="${X(n-1)+4}" y="${Y(last[se.key])+3}" style="fill:var(--text-primary)">${num(last[se.key])}</text>`; }); } }
  s+=`<line id="xh" x1="0" x2="0" y1="${m.t}" y2="${m.t+ih}" stroke="var(--axis)" stroke-dasharray="3 3" visibility="hidden"/>`;
  rows.forEach((r,i)=>{ s+=`<rect class="hit" data-i="${i}" x="${m.l+step*i}" y="${m.t}" width="${step}" height="${ih}" fill="transparent"/>`; });
  s+='</svg>'; el.innerHTML=s;
  const svg=el.querySelector('svg'), xh=svg.querySelector('#xh');
  svg.querySelectorAll('.hit').forEach(h=>{ h.addEventListener('mousemove',e=>{ const i=+h.dataset.i, r=rows[i];
      xh.setAttribute('x1',X(i)); xh.setAttribute('x2',X(i)); xh.setAttribute('visibility','visible');
      showTip(e, `<b>${fmtD(r.date)}</b><br>`+o.tip(r)); });
    h.addEventListener('mouseleave',()=>{ xh.setAttribute('visibility','hidden'); hideTip(); }); });
}
function barPath(x,y,w,h,r,fill,dir){ if(h<=0) return ''; r=Math.min(r,h);
  const d = dir==='up' ? `M${x},${y+h}V${y+r}Q${x},${y} ${x+r},${y}H${x+w-r}Q${x+w},${y} ${x+w},${y+r}V${y+h}Z`
                       : `M${x},${y}V${y+h-r}Q${x},${y+h} ${x+r},${y+h}H${x+w-r}Q${x+w},${y+h} ${x+w},${y+h-r}V${y}Z`;
  return `<path d="${d}" fill="${fill}"/>`; }
function niceTicks(a,b,n){ const span=b-a, st=Math.pow(10,Math.floor(Math.log10(span/n))), err=span/n/st;
  const step=st*(err>=7.5?10:err>=3.5?5:err>=1.5?2:1), t=[]; for(let v=Math.ceil(a/step)*step; v<=b+1e-9; v+=step) t.push(+v.toFixed(6)); return t; }

const D = DATA.days, L = DATA.load, last = arr => { for(let i=arr.length-1;i>=0;i--) if(arr[i]!=null) return arr[i]; return null; };
const C1='var(--s1)', C2='var(--s2)';
chart($('#c_sleep'),{rows:D,kind:'bar',series:[{key:'sleep_h',color:C1}],yMin:0,
  tip:r=>`Сон: <b>${num(r.sleep_h,1)} ч</b> · score ${num(r.sleep_score)}<br>Глубокий ${num(r.deep_h,1)} · Лёгкий ${num(r.light_h,1)} · REM ${num(r.rem_h,1)} · Бодр. ${num(r.awake_h,1)}`});
chart($('#c_score'),{rows:D,kind:'line',series:[{key:'sleep_score',color:C1}],floor:0,tip:r=>`Sleep score: <b>${num(r.sleep_score)}</b>`});
chart($('#c_hrv'),{rows:D,kind:'line',series:[{key:'hrv',color:C1}],band:{lo:'hrv_lo',hi:'hrv_hi'},floor:0,
  tip:r=>`HRV: <b>${num(r.hrv)} мс</b> · 7 дн. ${num(r.hrv_7d)}<br>Норма ${num(r.hrv_lo)}–${num(r.hrv_hi)} · ${r.hrv_status||''}`});
chart($('#c_rhr'),{rows:D,kind:'line',series:[{key:'rhr',color:C1}],tip:r=>`Пульс покоя: <b>${num(r.rhr)}</b>`});
chart($('#c_bb'),{rows:D,kind:'range',lo:'bb_low',hi:'bb_high',series:[{color:C1}],yMin:0,yMax:100,tip:r=>`Body Battery: <b>${num(r.bb_low)} → ${num(r.bb_high)}</b>`});
chart($('#c_stress'),{rows:D,kind:'bar',series:[{key:'stress',color:C1}],yMin:0,tip:r=>`Средний стресс: <b>${num(r.stress)}</b>`});
chart($('#c_steps'),{rows:D,kind:'bar',series:[{key:'steps',color:C1}],yMin:0,tip:r=>`Шаги: <b>${num(r.steps)}</b>`});
chart($('#c_load'),{rows:L,kind:'line',series:[{key:'ctl',color:C1},{key:'atl',color:C2}],floor:0,
  tip:r=>`<span class="dot" style="background:var(--s1)"></span>Fitness ${num(r.ctl,1)}<br><span class="dot" style="background:var(--s2)"></span>Fatigue ${num(r.atl,1)}<br>Нагрузка дня ${num(r.load)}`});
chart($('#c_tsb'),{rows:L,kind:'div',series:[{key:'tsb'}],tip:r=>`Form (TSB): <b>${num(r.tsb,1)}</b>`});

/* KPI tiles */
const R = DATA.readiness||{}, today = D[D.length-1]||{}, lt = L[L.length-1]||{};
const hrvVals = D.map(r=>r.hrv), hrvLast = last(hrvVals), hrvRow = [...D].reverse().find(r=>r.hrv!=null)||{};
const rhrBase = (()=>{ const v=D.slice(0,-1).map(r=>r.rhr).filter(x=>x!=null); return v.length? v.reduce((a,b)=>a+b,0)/v.length : null; })();
const st = (ok, txt) => `<span class="dot" style="background:var(${ok===true?'--good':ok===false?'--crit':'--warn'})"></span>${txt}`;
const tiles = [
  ['Готовность к тренировке', num(R.score), R.level ? st(R.score>=60?true:R.score<35?false:null, (R.level||'')+(R.feedback?' · '+R.feedback:'')) : ''],
  ['Sleep score', num(last(D.map(r=>r.sleep_score))), num(last(D.map(r=>r.sleep_h)),1)+' ч сна'],
  ['HRV прошлой ночью', hrvLast!=null? num(hrvLast)+' мс':'—', hrvRow.hrv_lo? st(hrvLast>=hrvRow.hrv_lo && hrvLast<=hrvRow.hrv_hi ? true : null, `норма ${num(hrvRow.hrv_lo)}–${num(hrvRow.hrv_hi)}`) : ''],
  ['Body Battery', num(today.bb_now ?? today.bb_high), `макс. сегодня ${num(today.bb_high)}`],
  ['Пульс покоя', num(last(D.map(r=>r.rhr))), rhrBase? `среднее за период ${num(rhrBase)}`:''],
  ['Form (TSB)', num(lt.tsb,1), lt.tsb==null?'': st(lt.tsb<-20?false:lt.tsb>15?null:true, lt.tsb<-20?'сильная усталость':lt.tsb>15?'свежесть / детренированность':'рабочая зона')],
];
$('#tiles').innerHTML = tiles.map(t=>`<div class="tile"><div class="label">${t[0]}</div><div class="val">${t[1]}</div><div class="sub">${t[2]}</div></div>`).join('');

/* Tables */
const A = DATA.activities||[];
$('#t_act').innerHTML = '<tr><th class="l">Дата</th><th class="l">Тренировка</th><th>Время, мин</th><th>Км</th><th>Темп</th><th>Ср. пульс</th><th>Нагрузка</th><th>Aerobic TE</th></tr>' +
  (A.length ? A.map(a=>`<tr><td>${(a.start||'').slice(0,16).replace('T',' ')}</td><td class="l">${esc(a.name||a.type||'')}</td><td>${num(a.duration_min)}</td><td>${num(a.distance_km,2)}</td><td>${a.avg_pace||'—'}</td><td>${num(a.avg_hr)}</td><td>${num(a.training_load)}</td><td>${num(a.aerobic_te,1)}</td></tr>`).join('')
   : '<tr><td class="l" colspan="8">Нет тренировок за период</td></tr>');
$('#t_days').innerHTML = '<tr><th class="l">Дата</th><th>Сон, ч</th><th>Score</th><th>HRV</th><th>Пульс покоя</th><th>BB мин–макс</th><th>Стресс</th><th>Шаги</th></tr>' +
  [...D].reverse().map(r=>`<tr><td>${r.date}</td><td>${num(r.sleep_h,1)}</td><td>${num(r.sleep_score)}</td><td>${num(r.hrv)}</td><td>${num(r.rhr)}</td><td>${num(r.bb_low)}–${num(r.bb_high)}</td><td>${num(r.stress)}</td><td>${num(r.steps)}</td></tr>`).join('');
function esc(s){ return String(s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
</script></body></html>"""


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    p = build(get_client(), n)
    print(f"Dashboard: {p}")
    if sys.platform == "darwin":
        os.system(f'open "{p}"')
