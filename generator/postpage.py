# -*- coding: utf-8 -*-
"""Server-rendered article page for the top-N posts (real p/<id>.html files).

These exist for SEO and for rich Telegram/WhatsApp link previews: a crawler
that cannot run JavaScript still sees the full caption, the image and the
correct <title>/og: tags.
"""

SHARE_LABEL = "\u0627\u0634\u062a\u0631\u0627\u06a9\u200c\u06af\u0630\u0627\u0631\u06cc:"
REL_LABEL = "\U0001F517 \u067e\u0633\u062a\u200c\u0647\u0627\u06cc \u0645\u0631\u062a\u0628\u0637"
COPY_LABEL = "\U0001F517 \u06a9\u067e\u06cc \u0644\u06cc\u0646\u06a9"


def share_block(url, title):
    """Telegram / WhatsApp / X / copy-link row. `url` may be empty (JS falls
    back to location.href at runtime)."""
    return f'''<div class="sharebar" data-url="{url}" data-title="{title}">
  <span class="shl">{SHARE_LABEL}</span>
  <a class="sh tg" data-net="tg" href="#" target="_blank" rel="noopener">\u2708\ufe0f \u062a\u0644\u06af\u0631\u0627\u0645</a>
  <a class="sh wa" data-net="wa" href="#" target="_blank" rel="noopener">\U0001F4AC \u0648\u0627\u062a\u0633\u0627\u067e</a>
  <a class="sh tw" data-net="tw" href="#" target="_blank" rel="noopener">\U0001D54F</a>
  <button class="sh cp" type="button" data-net="copy">{COPY_LABEL}</button>
</div>'''


SHARE_JS = r"""
(function(){
  function wire(bar){
    if(bar.dataset.wired)return; bar.dataset.wired='1';
    var u=bar.dataset.url||location.href, t=bar.dataset.title||document.title;
    var eu=encodeURIComponent(u), et=encodeURIComponent(t);
    var map={tg:'https://t.me/share/url?url='+eu+'&text='+et,
             wa:'https://wa.me/?text='+et+'%20'+eu,
             tw:'https://twitter.com/intent/tweet?url='+eu+'&text='+et};
    bar.querySelectorAll('[data-net]').forEach(function(el){
      var n=el.dataset.net;
      if(map[n]){el.href=map[n];return;}
      el.addEventListener('click',function(){
        var done=function(){el.classList.add('ok');
          var o=el.textContent; el.textContent='\u2713 \u06a9\u067e\u06cc \u0634\u062f';
          setTimeout(function(){el.textContent=o;el.classList.remove('ok');},1600);};
        if(navigator.clipboard&&navigator.clipboard.writeText)
          navigator.clipboard.writeText(u).then(done,done);
        else{var i=document.createElement('input');i.value=u;document.body.appendChild(i);
          i.select();try{document.execCommand('copy');}catch(e){}i.remove();done();}
      });
    });
  }
  function scan(){document.querySelectorAll('.sharebar').forEach(wire);}
  scan();
  new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});
})();
"""
