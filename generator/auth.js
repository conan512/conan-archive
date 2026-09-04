/* Admin gate for the dashboard.
   IMPORTANT: this is a static site — there is no server to check a password.
   The gate stores a SHA-256 hash and compares it in the browser, which keeps
   the page away from casual visitors, but a determined person can read the
   page source. Do not treat it as real security; the archive data itself is
   public anyway. See راهنمای-داشبورد.md for a properly private option. */
(function () {
  const HASH = "__HASH__";          // sha256(username + ":" + password)
  const KEY = "conan:admin";
  const TTL = 12 * 60 * 60 * 1000;  // stay signed in for 12h

  const gate = document.getElementById('gate');
  const panel = document.getElementById('dashpanel');
  if (!gate || !panel) return;

  async function sha256(txt) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(txt));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  function unlock() {
    gate.style.display = 'none';
    panel.style.display = '';
    document.body.classList.add('unlocked');
  }

  function lock() {
    try { localStorage.removeItem(KEY); } catch (e) {}
    location.reload();
  }

  // already signed in?
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const { h, t } = JSON.parse(raw);
      if (h === HASH && Date.now() - t < TTL) unlock();
      else localStorage.removeItem(KEY);
    }
  } catch (e) {}

  const form = document.getElementById('gateform');
  const err = document.getElementById('gateerr');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const u = document.getElementById('gu').value.trim();
    const p = document.getElementById('gp').value;
    const h = await sha256(u + ':' + p);
    if (h === HASH) {
      try { localStorage.setItem(KEY, JSON.stringify({ h, t: Date.now() })); } catch (e) {}
      err.style.display = 'none';
      unlock();
    } else {
      err.style.display = '';
      err.textContent = 'نام کاربری یا رمز عبور اشتباه است.';
      document.getElementById('gp').value = '';
    }
  });

  const out = document.getElementById('logout');
  if (out) out.addEventListener('click', lock);
})();
