/* Live visitor stats — reads the public GoatCounter counter endpoint.
   COUNTER is your GoatCounter site code (the subdomain of your panel URL).
   The JSON endpoint only works when "Allow public access" is enabled in
   GoatCounter → Settings → Site settings. Until then we show a hint. */
const COUNTER = "detectiveconanir";

const box = document.getElementById('livebox');
const N = n => (Number(n) || 0).toLocaleString('fa-IR');
const PANEL = `https://${COUNTER}.goatcounter.com`;

function kpi(icon, val, label) {
  return `<div class="kpi"><div class="ki">${icon}</div><b>${val}</b><span>${label}</span></div>`;
}

function note(msg) {
  return `<div class="note" style="margin:0">${msg}</div>`;
}

const panelLink =
  `<a href="${PANEL}" target="_blank" rel="noopener" style="color:var(--red2)">پنل GoatCounter ↗</a>`;

async function load() {
  if (!COUNTER) return;
  box.innerHTML = note('در حال دریافت آمار…');

  let total = null, unique = null;
  try {
    const r = await fetch(`${PANEL}/counter/TOTAL.json`);
    if (r.status === 403 || r.status === 404) {
      box.innerHTML = note(
        `آمار عمومی هنوز فعال نیست. در ${panelLink} برو به
         <b>Settings → Site settings</b> و گزینهٔ
         <b>Allow public access to summary statistics</b> را تیک بزن،
         سپس این صفحه را رفرش کن.`);
      return;
    }
    if (!r.ok) throw new Error('http ' + r.status);
    const d = await r.json();
    total = d.count;
    unique = d.count_unique ?? d.count;
  } catch (e) {
    box.innerHTML = note(
      `دریافت آمار ممکن نشد. اگر تازه سرویس را فعال کرده‌اید ممکن است هنوز
       داده‌ای ثبت نشده باشد، یا دسترسی شبکه محدود باشد. ${panelLink}`);
    return;
  }

  box.innerHTML =
    `<div class="kpis">
       ${kpi('👥', N(unique), 'بازدیدکنندهٔ یکتا')}
       ${kpi('👁', N(total), 'کل بازدید صفحات')}
     </div>
     <p style="font-size:.84rem;color:var(--dim);margin-top:14px;line-height:1.9">
       نمودار روزانه، <b>آمار تک‌تک صفحات</b>، کشور، مرورگر و منبع ورود
       را در ${panelLink} ببینید.
     </p>`;
}

load();
