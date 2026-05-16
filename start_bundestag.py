#!/usr/bin/env python3
"""Bundestag OpenData Explorer — avvia con: python3 avvia_bundestag.py"""
import http.server, urllib.request, urllib.parse, json
import threading, webbrowser, time, os, datetime, re

PORT       = 8765
API_KEY    = "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"
DIP_BASE   = "https://search.dip.bundestag.de/api/v1"
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bundestag_export")
os.makedirs(EXPORT_DIR, exist_ok=True)

LEGS = [
    (21,'2025-'),
    (20,'2021-2025'),
    (19,'2017-2021'),
    (18,'2013-2017'),
    (17,'2009-2013'),
    (16,'2005-2009'),
    (15,'2002-2005'),
    (14,'1998-2002'),
    (13,'1994-1998'),
    (12,'1990-1994'),
    (11,'1987-1990'),
    (10,'1983-1987'),
    (9,'1980-1983'),
    (8,'1976-1980'),
    (7,'1972-1976'),
    (6,'1969-1972'),
    (5,'1965-1969'),
    (4,'1961-1965'),
    (3,'1957-1961'),
    (2,'1953-1957'),
    (1,'1949-1953'),
]

def wp_options():
    o = ['<option value="">All</option>']
    for n,y in LEGS:
        o.append('<option value="%d">%d\u00aa (%s)</option>' % (n,n,y))
    return ''.join(o)

def wp_tabs(ds, lid, gid, lo=1, hi=21):
    t = []
    for n,_ in LEGS:
        if n < lo or n > hi: continue
        ac = ' class="wpt on"' if n == hi else ' class="wpt"'
        cb = 'loadIdx(&quot;%s&quot;,&quot;%s&quot;,%d,this,&quot;%s&quot;)' % (ds,lid,n,gid)
        t.append('<button%s onclick="%s">%d\u00aa</button>' % (ac,cb,n))
    return ''.join(t)

WPO = wp_options()
PT  = wp_tabs('plenarprotokoll','prot-list','prot-tg')
DT  = wp_tabs('drucksache','druck-list','druck-tg')
VT  = wp_tabs('vorgang','vorg-list','vorg-tg', lo=8)
TODAY = datetime.date.today().isoformat()

CSS = '''
:root{--bg:#f4efe6;--sf:#fffdf7;--s2:#ede7d5;--bd:#d3c8ae;--ac:#1a3a5c;--rd:#c0392b;--go:#b8860b;--gr:#2e7d32;--tx:#1a1a1a;--mu:#7a7060;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--tx);font-family:'IBM Plex Sans',sans-serif;min-height:100vh;}
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
header{background:var(--ac);color:#fff;padding:0 28px;display:flex;align-items:center;gap:14px;height:58px;border-bottom:4px solid var(--go);}
h1{font-size:17px;font-weight:700;}h1 em{color:var(--go);font-style:normal;}
.hp{margin-left:auto;font-size:11px;opacity:.5;font-family:'IBM Plex Mono',monospace;}
.wrap{max-width:1160px;margin:0 auto;padding:24px;display:flex;flex-direction:column;gap:18px;}
.tabs{display:flex;border-bottom:2px solid var(--bd);}
.tab{background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:10px 20px;font-size:13px;font-weight:600;color:var(--mu);cursor:pointer;white-space:nowrap;transition:color .15s,border-color .15s;}
.tab:hover{color:var(--ac);}.tab.on{color:var(--ac);border-bottom-color:var(--ac);}
.pnl{display:none;flex-direction:column;gap:18px;}.pnl.on{display:flex;}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:18px;}
.row{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;}
.fld{display:flex;flex-direction:column;gap:5px;}
.fld label{font-size:10px;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:1px;}
input,select{background:var(--bg);border:1px solid var(--bd);border-radius:6px;padding:8px 10px;font-family:'IBM Plex Mono',monospace;font-size:13px;color:var(--tx);outline:none;}
input:focus,select:focus{border-color:var(--ac);}
.btn{background:var(--ac);color:#fff;border:none;border-radius:6px;padding:9px 18px;font-weight:700;font-size:13px;cursor:pointer;transition:background .2s;}
.btn:hover{background:#0d2440;}.btn:disabled{opacity:.5;cursor:wait;}
.btn2{background:transparent;border:2px solid var(--ac);color:var(--ac);}.btn2:hover{background:var(--ac);color:#fff;}
.btng{background:var(--gr);}.btng:hover{background:#1b5e20;}
.dsg{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.ds{background:var(--sf);border:2px solid var(--bd);border-radius:8px;padding:14px 10px;cursor:pointer;text-align:center;transition:border-color .15s,transform .15s;}
.ds:hover{border-color:var(--ac);transform:translateY(-2px);}.ds.on{border-color:var(--ac);background:var(--ac);color:#fff;}
.ds.on .dss{color:rgba(255,255,255,.7);}
.dsi{font-size:24px;margin-bottom:5px;display:block;}.dsn{font-weight:700;font-size:13px;margin-bottom:2px;}
.dss{font-size:11px;color:var(--mu);font-family:'IBM Plex Mono',monospace;}
.ib{background:var(--s2);border:1px solid var(--bd);border-radius:8px;padding:10px 16px;display:none;gap:16px;font-size:12px;font-family:'IBM Plex Mono',monospace;flex-wrap:wrap;align-items:center;}
.il{color:var(--mu);}.iv{font-weight:700;color:var(--ac);}
#results{display:flex;flex-direction:column;gap:10px;}
.rc{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:16px;transition:border-color .15s;animation:fu .2s ease;}
.rc:hover{border-color:var(--ac);}
@keyframes fu{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.rh{display:flex;gap:9px;margin-bottom:7px;align-items:flex-start;}
.rt{background:var(--ac);color:#fff;font-family:'IBM Plex Mono',monospace;font-size:10px;padding:2px 7px;border-radius:4px;flex-shrink:0;}
.rt.d{background:var(--rd);}.rt.p{background:var(--gr);}
.rn{font-weight:600;font-size:14px;line-height:1.4;color:var(--ac);}
.rm{display:flex;gap:12px;flex-wrap:wrap;font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--mu);margin-bottom:5px;}
.rb{font-size:12px;line-height:1.6;color:#444;border-left:3px solid var(--bd);padding-left:9px;margin-top:6px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;}
.rl{display:flex;gap:6px;margin-top:9px;flex-wrap:wrap;}
.rlk{font-size:11px;font-family:'IBM Plex Mono',monospace;padding:3px 9px;border-radius:20px;border:1px solid var(--bd);color:var(--ac);text-decoration:none;background:var(--bg);}
.rlk:hover{background:var(--ac);color:#fff;}
.pg{display:none;justify-content:center;gap:7px;align-items:center;}
.pgb{background:var(--sf);border:1px solid var(--bd);color:var(--mu);padding:5px 13px;border-radius:6px;font-size:13px;cursor:pointer;}
.pgb:hover{background:var(--ac);color:#fff;border-color:var(--ac);}.pgb:disabled{opacity:.3;cursor:default;}
.pgg{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;}
.pc{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:13px;display:flex;gap:11px;}
.pav{width:42px;height:42px;border-radius:50%;background:var(--ac);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:15px;flex-shrink:0;}
.pnm{font-weight:700;font-size:13px;color:var(--ac);margin-bottom:2px;}.psu{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--mu);}
#loading{display:none;text-align:center;padding:36px;}
.spin{width:30px;height:30px;border:3px solid var(--bd);border-top-color:var(--ac);border-radius:50%;animation:sp .8s linear infinite;margin:0 auto 10px;}
@keyframes sp{to{transform:rotate(360deg)}}
#err{display:none;background:#fdf0f0;border:1px solid #e57373;border-radius:8px;padding:13px 16px;color:var(--rd);font-size:13px;}
#empty{display:none;text-align:center;padding:36px;color:var(--mu);font-size:14px;}
.st{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--mu);padding-bottom:6px;border-bottom:2px solid var(--bd);margin-bottom:10px;}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;}
.sc{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:13px 15px;}
.si{font-size:20px;margin-bottom:4px;}.sl{font-size:10px;color:var(--mu);text-transform:uppercase;letter-spacing:1px;font-weight:700;}
.sv{font-size:20px;font-weight:700;color:var(--ac);font-family:'IBM Plex Mono',monospace;}.ss{font-size:11px;color:var(--mu);}
.is{background:var(--sf);border:1px solid var(--bd);border-radius:8px;overflow:hidden;}
.ih{background:var(--s2);border-bottom:1px solid var(--bd);padding:11px 16px;display:flex;align-items:center;gap:10px;cursor:pointer;user-select:none;transition:background .12s;}
.ih:hover{background:#d9d2be;}.iit{font-size:18px;}.itn{font-weight:700;font-size:14px;color:var(--ac);flex:1;}
.icn{font-size:11px;font-family:'IBM Plex Mono',monospace;color:#fff;background:var(--ac);padding:2px 8px;border-radius:20px;}
.ich{font-size:11px;color:var(--mu);transition:transform .2s;}.is.op .ich{transform:rotate(90deg);}
.ibdy{display:none;}.is.op .ibdy{display:block;}
.ifl{background:var(--bg);padding:8px 16px;display:flex;align-items:center;gap:6px;border-bottom:1px solid var(--bd);flex-wrap:wrap;}
.ifl-l{font-size:10px;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:1px;white-space:nowrap;}
.wpts{display:flex;gap:3px;flex-wrap:wrap;}
.wpt{background:var(--sf);border:1px solid var(--bd);border-radius:5px;padding:2px 8px;font-family:'IBM Plex Mono',monospace;font-size:11px;cursor:pointer;color:var(--ac);font-weight:600;}
.wpt:hover,.wpt.on{background:var(--ac);color:#fff;border-color:var(--ac);}
.ii{display:flex;align-items:center;gap:11px;padding:10px 16px;border-bottom:1px solid var(--bd);cursor:pointer;transition:background .1s;}
.ii:last-child{border-bottom:none;}.ii:hover{background:rgba(26,58,92,.04);}
.inum{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--mu);min-width:26px;text-align:right;flex-shrink:0;}
.iinf{flex:1;min-width:0;}.itit{font-size:13px;font-weight:600;color:var(--ac);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.imet{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--mu);margin-top:2px;}
.ibdg{font-size:10px;font-family:'IBM Plex Mono',monospace;padding:2px 7px;border-radius:4px;background:var(--ac);color:#fff;flex-shrink:0;}
.ibdg.g{background:var(--gr);}.ibdg.r{background:var(--rd);}.ibdg.gd{background:var(--go);color:#000;}
.iarr{font-size:12px;color:var(--bd);flex-shrink:0;}.ii:hover .iarr{color:var(--ac);}
.iload{padding:22px;text-align:center;color:var(--mu);font-size:13px;display:flex;align-items:center;justify-content:center;gap:7px;}
.iempty{padding:18px;text-align:center;color:var(--mu);font-size:13px;}
.mspin{width:15px;height:15px;border:2px solid var(--bd);border-top-color:var(--ac);border-radius:50%;animation:sp .8s linear infinite;flex-shrink:0;}
.ab{display:flex;gap:3px;flex-wrap:wrap;}
.abb{background:var(--sf);border:1px solid var(--bd);border-radius:4px;padding:2px 7px;font-family:'IBM Plex Mono',monospace;font-size:11px;cursor:pointer;color:var(--ac);}
.abb:hover,.abb.on{background:var(--ac);color:#fff;border-color:var(--ac);}
.expw{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
@media(max-width:680px){.expw{grid-template-columns:1fr;}}
.expf{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:20px;display:flex;flex-direction:column;gap:14px;}
.expf h2{font-size:14px;font-weight:700;color:var(--ac);}
.expf p{font-size:12px;color:#555;line-height:1.5;}
.expr{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:20px;display:flex;flex-direction:column;gap:14px;}
.expr h2{font-size:14px;font-weight:700;color:var(--ac);}
.exp-tabs{display:flex;gap:0;border-bottom:2px solid var(--bd);margin-bottom:14px;}
.exp-tab{background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;padding:8px 16px;font-size:12px;font-weight:700;color:var(--mu);cursor:pointer;white-space:nowrap;}
.exp-tab:hover{color:var(--ac);}.exp-tab.on{color:var(--ac);border-bottom-color:var(--ac);}
.expsub{display:none;flex-direction:column;gap:12px;}.expsub.on{display:flex;}
.pw{background:var(--bd);border-radius:20px;height:10px;overflow:hidden;}
.pb{background:var(--ac);height:10px;border-radius:20px;width:0%;transition:width .4s;}
.pb.done{background:var(--gr);}
.plog{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--mu);max-height:200px;overflow-y:auto;line-height:1.9;border:1px solid var(--bd);border-radius:6px;padding:9px;background:var(--bg);}
.eres{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:16px;display:none;flex-direction:column;gap:10px;}
.eres h3{color:var(--gr);font-size:14px;}
.einfo{font-size:13px;color:#333;line-height:1.7;}
.nlm{background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:11px 13px;font-size:12px;color:#5d4037;line-height:1.7;}
.nlm strong{color:#7a5700;}
.hint{font-size:11px;color:var(--mu);margin-top:3px;}
'''

JS = r'''
window.onload = function() {

  // STATE
  var curDs   = 'plenarprotokoll';
  var curStk  = [], curCur = null, curPg = 1, totFd = 0;
  var idxDone = false;

  // ── PANEL SWITCH ──────────────────────────────────────────────────────────
  window.showPanel = function(name) {
    var PANELS = ['search','index','export'];
    PANELS.forEach(function(p, i) {
      document.getElementById('pnl-' + p).className = 'pnl' + (p === name ? ' on' : '');
      document.querySelectorAll('.tab')[i].className = 'tab' + (PANELS[i] === name ? ' on' : '');
    });
    if (name === 'index' && !idxDone) { idxDone = true; initIdx(); }
  };

  // ── DATASET SELECT ────────────────────────────────────────────────────────
  window.setDs = function(ds, el) {
    curDs = ds;
    document.querySelectorAll('.ds').forEach(function(c) { c.classList.remove('on'); });
    el.classList.add('on');
    doSearch(); // rilancia la ricerca col nuovo dataset
  };

  // ── SEARCH ────────────────────────────────────────────────────────────────
  window.doSearch = function(cf) {
    var q   = document.getElementById('q').value.trim();
    var wp  = document.getElementById('wp').value;
    var num = parseInt(document.getElementById('num').value) || 10;
    if (!cf) { curStk = []; curCur = null; curPg = 1; }
    sEl('loading');
    document.getElementById('search-btn').disabled = true;

    if (q) {
      // Full-text search via server-side /search endpoint
      // Uses drucksache-text / plenarprotokoll-text which contain full OCR text
      doFullTextSearch(q, wp, num, cf);
    } else {
      // No keyword: browse by date/wp via standard API
      var p = { num: num };
      if (wp) p['f.wahlperiode'] = wp;
      if (cf) p['cursor']        = cf;
      dip(curDs, p)
        .then(function(d) {
          totFd  = d.numFound || 0;
          curCur = d.cursor   || null;
          renderRes(d, ''); updIB('', wp);
        })
        .catch(function(e) { sErr(e.message); })
        .finally(function() {
          document.getElementById('search-btn').disabled = false;
          sEl('results');
        });
    }
  };

  function doFullTextSearch(q, wp, num, cursor) {
    // Stream results from /search — server paginates -text endpoint and filters
    var qs = 'q=' + encodeURIComponent(q)
      + '&dataset=' + encodeURIComponent(curDs)
      + '&num='     + encodeURIComponent(num);
    if (wp)     qs += '&wp='        + encodeURIComponent(wp);
    if (cursor) qs += '&cursor='    + encodeURIComponent(cursor);

    // Show scanning status
    var status = document.getElementById('results');
    status.innerHTML = '<div style="color:var(--mu);font-size:13px;padding:10px 0">'
      + '<div class="spin" style="width:20px;height:20px;margin:0 8px 0 0;display:inline-block;vertical-align:middle"></div>'
      + 'Full-text scan in progress... (may take a few seconds)</div>';
    status.style.display = 'flex';

    fetch('/search?' + qs).then(function(res) {
      var reader = res.body.getReader();
      var dec    = new TextDecoder();
      var buf    = '';
      function read() {
        return reader.read().then(function(chunk) {
          if (chunk.done) {
            document.getElementById('search-btn').disabled = false;
            return;
          }
          buf += dec.decode(chunk.value, { stream: true });
          var lines = buf.split('\n'); buf = lines.pop();
          lines.forEach(function(line) {
            if (!line.trim()) return;
            try {
              var msg = JSON.parse(line);
              if (msg.type === 'progress') {
                status.innerHTML = '<div style="color:var(--mu);font-size:13px;padding:4px 0">'
                  + '&#128269; ' + msg.text + '</div>';
              } else if (msg.type === 'results') {
                document.getElementById('search-btn').disabled = false;
                totFd  = msg.numFound;
                curCur = msg.cursor || null;
                renderRes(msg, q);
                updIB(q, wp);
                sEl('results');
              } else if (msg.type === 'error') {
                sErr(msg.text);
                document.getElementById('search-btn').disabled = false;
              }
            } catch(e) {}
          });
          return read();
        });
      }
      return read();
    }).catch(function(e) {
      sErr('Errore connessione: ' + e.message);
      document.getElementById('search-btn').disabled = false;
    });
  }

  function renderRes(d, q) {
    var c     = document.getElementById('results');
    var items = d.documents || [];

    if (!items.length) {
      sEl('empty');
      document.getElementById('empty').innerHTML = q
        ? 'No documents found for <strong>"' + q + '"</strong>'
          + ' (scanned ' + (d.scanned || 0).toLocaleString('it') + ' documents).'
        : 'No results found.';
      c.innerHTML = '';
      document.getElementById('pagination').style.display = 'none'; return;
    }
    hEl('empty');

    var info;
    if (q) {
      info = items.length + ' full-text results for &ldquo;' + q + '&rdquo;'
        + ' (scanned ' + (d.scanned || 0).toLocaleString('it')
        + ' of ' + (d.total || 0).toLocaleString('it') + ')';
    } else {
      info = totFd.toLocaleString('it') + ' results &mdash; page' + curPg;
    }

    if (curDs === 'person') {
      c.innerHTML = '<div class="st">' + items.length + ' members</div>'
        + '<div class="pgg">' + items.map(rPer).join('') + '</div>';
    } else {
      c.innerHTML = '<div class="st">' + info + '</div>' + items.map(rCard).join('');
    }
    renderPg(d);
  }

  function rCard(docs) {
    var title = doc.titel || doc.betreff || doc.dokumentnummer || '(senza titolo)';
    var cls   = curDs === 'plenarprotokoll' ? 'p' : curDs === 'drucksache' ? 'd' : '';
    var lbl   = curDs === 'plenarprotokoll' ? 'PROTOKOLL' : curDs === 'drucksache' ? 'DRUCKSACHE' : 'VORGANG';
    var meta  = [];
    if (doc.datum)           meta.push('&#128197; ' + doc.datum.slice(0,10));
    if (doc.wahlperiode)     meta.push('Term ' + doc.wahlperiode);
    if (doc.dokumentnummer)  meta.push('&#8470; ' + doc.dokumentnummer);
    if (doc.drucksachetyp)   meta.push(doc.drucksachetyp);
    if (doc.vorgangstyp)     meta.push(doc.vorgangstyp);
    if (doc.autoren_anzeige) meta.push('&#9997; ' + doc.autoren_anzeige.slice(0,2).join(', '));
    var body  = doc.snippet  || doc.abstract || doc.beschreibung || '';
    var links = '';
    if (doc.fundstelle && doc.fundstelle.pdf_url)
      links += '<a class="rlk" href="' + doc.fundstelle.pdf_url + '" target="_blank">&#128229; PDF</a>';
    if (doc.id)
      links += '<a class="rlk" href="https://dip.bundestag.de/vorgang/x/' + doc.id + '" target="_blank">&#128279; DIP</a>';
    return '<div class="rc">'
      + '<div class="rh"><span class="rt ' + cls + '">' + lbl + '</span>'
      + '<div class="rn">' + title + '</div></div>'
      + '<div class="rm">' + meta.join(' &middot; ') + '</div>'
      + (body  ? '<div class="rb">' + body  + '</div>' : '')
      + (links ? '<div class="rl">' + links + '</div>' : '')
      + '</div>';
  }

  function rPer(p) {
    var name = ((p.vorname || '') + ' ' + (p.nachname || '')).trim() || '--';
    var ini  = name.split(' ').map(function(w) { return w[0]; }).slice(0,2).join('').toUpperCase();
    var par  = (p.basisdaten && p.basisdaten.fraktion) || p.fraktion || '--';
    var wp   = p.wahlperiode ? 'Term ' + p.wahlperiode : '';
    var wk   = p.wahlkreis_name || '';
    return '<div class="pc"><div class="pav">' + ini + '</div><div>'
      + '<div class="pnm">' + name + '</div>'
      + '<div class="psu">' + par + (wp ? ' - ' + wp : '') + '</div>'
      + (wk ? '<div class="psu">' + wk + '</div>' : '')
      + '</div></div>';
  }

  function renderPg(d) {
    var pg  = document.getElementById('pagination');
    var hn  = !!d.cursor, hp = curStk.length > 0;
    if (!hn && !hp) { pg.style.display = 'none'; return; }
    pg.style.display = 'flex';
    pg.innerHTML =
      '<button class="pgb" onclick="goBack()" ' + (!hp ? 'disabled' : '') + '>&#8249; Prev</button>'
      + '<span style="font-size:13px;color:var(--mu);padding:0 8px;align-self:center">Page ' + curPg + '</span>'
      + '<button class="pgb" onclick="goNext(\'' + (d.cursor||'') + '\')" ' + (!hn ? 'disabled' : '') + '>Next &#8250;</button>';
  }

  window.goNext = function(c) {
    if (!c) return;
    curStk.push(curCur); curPg++;
    doSearch(c);
  };
  window.goBack = function()  { if (!curStk.length) return; var p = curStk.pop(); curPg--; doSearch(p || undefined); };

  function updIB(q, wp) {
    document.getElementById('ib').style.display = 'flex';
    document.getElementById('ib-ds').textContent  = curDs;
    document.getElementById('ib-tot').textContent = totFd.toLocaleString('it');
    document.getElementById('ib-pg').textContent  = curPg;
    document.getElementById('ib-q').textContent   = q || (wp ? 'Term ' + wp : '(tutti)');
  }

  window.resetSearch = function() {
    document.getElementById('q').value  = '';
    document.getElementById('wp').value = '';
    document.getElementById('results').innerHTML = '';
    document.getElementById('ib').style.display         = 'none';
    document.getElementById('pagination').style.display = 'none';
    hEl('empty'); hEl('loading'); hEl('err');
    curStk = []; curPg = 1;
  };

  // ── INDEX ─────────────────────────────────────────────────────────────────
  function initIdx() {
    lCount('plenarprotokoll', 'sv-prot',  'icn-prot');
    lCount('drucksache',      'sv-druck', 'icn-druck');
    lCount('person',          'sv-pers',  'icn-pers');
    lCount('vorgang',         'sv-vorg',  'icn-vorg');
    buildAB();
    var fb = document.querySelector('#prot-tg .wpt');
    if (fb) loadIdx('plenarprotokoll', 'prot-list', 21, fb, 'prot-tg');
  }

  function lCount(ds, svId, icId) {
    dip(ds, { num: 1 }).then(function(d) {
      var n = (d.numFound || 0).toLocaleString('it');
      document.getElementById(svId).textContent = n;
      document.getElementById(icId).textContent = n;
    }).catch(function() { document.getElementById(svId).textContent = '--'; });
  }

  window.toggleSec = function(id) { document.getElementById(id).classList.toggle('op'); };

  window.loadIdx = function(ds, lid, wp, btn, gid) {
    document.querySelectorAll('#' + gid + ' .wpt').forEach(function(b) { b.classList.remove('on'); });
    if (btn) btn.classList.add('on');
    var el = document.getElementById(lid);
    el.innerHTML = '<div class="iload"><div class="mspin"></div> Loading term ' + wp + '...</div>';
    dip(ds, { num: 50, 'f.wahlperiode': wp }).then(function(d) {
      var items = d.documents || [];
      if (!items.length) { el.innerHTML = '<div class="iempty">No documents.</div>'; return; }
      el.innerHTML = items.map(function(doc, i) { return rIR(ds, doc, i, wp); }).join('');
    }).catch(function(e) {
      el.innerHTML = '<div class="iempty" style="color:var(--rd)">' + e.message + '</div>';
    });
  };

  function rIR(ds, doc, i, wp) {
    var date  = (doc.datum || '').slice(0,10) || '--';
    var num   = doc.dokumentnummer || '';
    var title = doc.titel || doc.betreff || 'Doc ' + (i+1);
    var badge, bc, fn;
    if (ds === 'plenarprotokoll') {
      badge = 'PROTOKOLL'; bc = 'g';
      fn = 'jumpSearch("plenarprotokoll","' + esc(num) + '",' + wp + ')';
    } else if (ds === 'drucksache') {
      var typ = doc.drucksachetyp || 'Drucksache';
      badge = typ.slice(0,12).toUpperCase();
      bc = typ.toLowerCase().indexOf('anfrage') >= 0 ? 'gd' : 'r';
      fn = 'jumpSearch("drucksache","' + esc(num) + '",' + wp + ')';
    } else {
      badge = 'VORGANG'; bc = '';
      fn = 'jumpSearch("vorgang","' + esc(title.slice(0,35)) + '",' + wp + ')';
    }
    return '<div class="ii" onclick="' + fn + '">'
      + '<span class="inum">' + (i+1) + '</span>'
      + '<div class="iinf"><div class="itit">' + title + '</div>'
      + '<div class="imet">&#128197; ' + date + ' &middot; &#8470; ' + num
      + ' &middot; Term ' + (doc.wahlperiode || wp) + '</div></div>'
      + '<span class="ibdg ' + bc + '">' + badge + '</span>'
      + '<span class="iarr">&#8594;</span></div>';
  }

  function buildAB() {
    var bar = document.getElementById('alpha-bar');
    bar.innerHTML = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(function(l) {
      return '<button class="abb" onclick="loadPIdx(\'' + l + '\',this)">' + l + '</button>';
    }).join('');
  }

  window.loadPIdx = function(letter, btn) {
    document.querySelectorAll('#alpha-bar .abb').forEach(function(b) { b.classList.remove('on'); });
    btn.classList.add('on');
    var el = document.getElementById('pers-list');
    el.innerHTML = '<div class="iload"><div class="mspin"></div> Loading ' + letter + '...</div>';
    dip('person', { num: 50, 'f.nachname': letter + '*' }).then(function(d) {
      var items = d.documents || [];
      if (!items.length) {
        el.innerHTML = '<div class="iempty">No member found for ' + letter + '</div>'; return;
      }
      el.innerHTML = items.map(function(p, i) {
        var name = ((p.vorname || '') + ' ' + (p.nachname || '')).trim() || '--';
        var par  = (p.basisdaten && p.basisdaten.fraktion) || p.fraktion || '--';
        var wp   = p.wahlperiode ? 'Term ' + p.wahlperiode : '';
        var wk   = p.wahlkreis_name || '';
        return '<div class="ii" onclick="jumpSearchPer(\'' + esc(name) + '\')">'
          + '<span class="inum">' + (i+1) + '</span>'
          + '<div class="iinf"><div class="itit">' + name + '</div>'
          + '<div class="imet">' + par + (wp ? ' - ' + wp : '') + (wk ? ' - ' + wk : '') + '</div></div>'
          + '<span class="ibdg gd">MdB</span><span class="iarr">&#8594;</span></div>';
      }).join('');
    }).catch(function(e) {
      el.innerHTML = '<div class="iempty" style="color:var(--rd)">' + e.message + '</div>';
    });
  };

  window.jumpSearch = function(ds, q, wp) {
    curDs = ds;
    document.querySelectorAll('.ds').forEach(function(c) { c.classList.remove('on'); });
    var map = { plenarprotokoll: 0, drucksache: 1, person: 2, vorgang: 3 };
    var cards = document.querySelectorAll('.ds');
    if (cards[map[ds]]) cards[map[ds]].classList.add('on');
    document.getElementById('q').value  = q  || '';
    document.getElementById('wp').value = wp || '';
    showPanel('search'); doSearch();
  };

  window.jumpSearchPer = function(name) {
    curDs = 'person';
    document.querySelectorAll('.ds').forEach(function(c) { c.classList.remove('on'); });
    document.querySelectorAll('.ds')[2].classList.add('on');
    document.getElementById('q').value  = name;
    document.getElementById('wp').value = '';
    showPanel('search'); doSearch();
  };

  // ── EXPORT ────────────────────────────────────────────────────────────────
  window.expTab = function(name, btn) {
    document.querySelectorAll('.exp-tab').forEach(function(b) { b.classList.remove('on'); });
    btn.classList.add('on');
    document.querySelectorAll('.expsub').forEach(function(el) { el.classList.remove('on'); });
    var sub = document.getElementById('sub-' + name);
    if (sub) sub.classList.add('on');
  };

  function expLog(msg) {
    var el = document.getElementById('plog');
    el.innerHTML += msg + '<br>'; el.scrollTop = el.scrollHeight;
  }
  function expBar(pct) {
    document.getElementById('pb').style.width = Math.min(pct, 100) + '%';
  }
  function expReset(btnId) {
    document.getElementById(btnId).disabled = true;
    document.getElementById('eres').style.display = 'none';
    document.getElementById('pb').style.width    = '0%';
    document.getElementById('pb').className      = 'pb';
    document.getElementById('plog').innerHTML    = '';
  }
  function expStream(qs, btnId, onDone) {
    fetch('/export?' + qs).then(function(res) {
      var reader = res.body.getReader();
      var dec    = new TextDecoder();
      var buf    = '';
      var last   = null;
      function read() {
        return reader.read().then(function(chunk) {
          if (chunk.done) { if (last) onDone(last); return; }
          buf += dec.decode(chunk.value, { stream: true });
          var lines = buf.split('\n'); buf = lines.pop();
          lines.forEach(function(line) {
            if (!line.trim()) return;
            try {
              var msg = JSON.parse(line);
              if (msg.type === 'progress') { expLog(msg.text); if (msg.pct !== undefined) expBar(msg.pct); }
              else if (msg.type === 'done')  { last = msg; }
              else if (msg.type === 'error') { expLog('ERR: ' + msg.text); }
            } catch(e) {}
          });
          return read();
        });
      }
      return read();
    }).catch(function(e) {
      expLog('Connection error: ' + e.message);
      document.getElementById(btnId).disabled = false;
    });
  }

  // TXT export
  window.startExport = function() {
    var ds   = document.getElementById('ex-ds').value;
    var from = document.getElementById('ex-from').value;
    var to   = document.getElementById('ex-to').value;
    var wp   = document.getElementById('ex-wp').value;
    var q    = document.getElementById('ex-q').value.trim();
    var max  = document.getElementById('ex-max').value;
    if (!from) { alert('Inserisci la data di inizio.'); return; }
    expReset('ex-btn');
    expLog('Starting TXT: ' + ds + ' | ' + from + ' - ' + to);
    var qs = 'mode=txt&dataset=' + encodeURIComponent(ds)
      + '&date_from=' + encodeURIComponent(from) + '&date_to=' + encodeURIComponent(to)
      + '&max=' + encodeURIComponent(max);
    if (wp) qs += '&wp='    + encodeURIComponent(wp);
    if (q)  qs += '&query=' + encodeURIComponent(q);
    expStream(qs, 'ex-btn', function(msg) {
      fetch('/download?file=' + encodeURIComponent(msg.filename))
        .then(function(r) { return r.blob(); })
        .then(function(blob) {
          var url = URL.createObjectURL(blob);
          var a   = document.createElement('a');
          a.href = url; a.download = msg.filename; a.click(); URL.revokeObjectURL(url);
        });
      document.getElementById('pb').className = 'pb done';
      document.getElementById('einfo').innerHTML =
        'Documents: <strong>' + msg.count + '</strong><br>'
        + 'File: <strong>' + msg.filename + '</strong><br>'
        + 'Dimensione: <strong>' + msg.size + '</strong>';
      document.getElementById('eres').style.display = 'flex';
      document.getElementById('ex-btn').disabled = false;
    });
  };

  // PDF download
  window.startPdfDownload = function() {
    var ds   = document.getElementById('pdf-ds').value;
    var from = document.getElementById('pdf-from').value;
    var to   = document.getElementById('pdf-to').value;
    var wp   = document.getElementById('pdf-wp').value;
    var q    = document.getElementById('pdf-q').value.trim();
    var max  = document.getElementById('pdf-max').value;
    if (!from) { alert('Inserisci la data di inizio.'); return; }
    expReset('pdf-btn');
    expLog('Starting PDF:    ' + ds + ' | ' + from + ' - ' + to);
    var qs = 'mode=pdf&dataset=' + encodeURIComponent(ds)
      + '&date_from=' + encodeURIComponent(from) + '&date_to=' + encodeURIComponent(to)
      + '&max=' + encodeURIComponent(max);
    if (wp) qs += '&wp='    + encodeURIComponent(wp);
    if (q)  qs += '&query=' + encodeURIComponent(q);
    expStream(qs, 'pdf-btn', function(msg) {
      document.getElementById('pb').className = 'pb done';
      document.getElementById('einfo').innerHTML =
        'PDFs downloaded: <strong>' + msg.count + '</strong><br>'
        + 'Folder: <strong>' + msg.folder + '</strong><br>'
        + 'Total: <strong>' + msg.size + '</strong>';
      document.getElementById('eres').style.display = 'flex';
      document.getElementById('pdf-btn').disabled = false;
    });
  };

  // ── UTILS ─────────────────────────────────────────────────────────────────
  function dip(ep, params) {
    var qs = Object.keys(params).map(function(k) {
      return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
    }).join('&');
    return fetch('/api/' + ep + '?' + qs).then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function esc(s) { return String(s).replace(/[<>&"']/g, ''); }

  function sEl(id) {
    ['loading','results','empty','err'].forEach(function(i) {
      var e = document.getElementById(i); if (e) e.style.display = 'none';
    });
    var e = document.getElementById(id); if (!e) return;
    if (id === 'results') { e.style.display = 'flex'; e.style.flexDirection = 'column'; }
    else e.style.display = 'block';
  }
  function hEl(id) { var e = document.getElementById(id); if (e) e.style.display = 'none'; }
  function sErr(msg) {
    hEl('loading'); hEl('empty'); hEl('results');
    var e = document.getElementById('err');
    e.textContent = msg; e.style.display = 'block';
  }

  doSearch();
};
'''

def build_html():
    h = []
    a = h.append
    a('<!DOCTYPE html>')
    a('<html lang="it">')
    a('<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    a('<title>Bundestag OpenData Explorer</title>')
    a('<style>' + CSS + '</style>')
    a('</head><body>')
    a('<header><span style="font-size:24px">&#127926;</span>')
    a('<h1>Bundestag <em>OpenData</em> Explorer</h1>')
    a('<span class="hp">localhost:' + str(PORT) + '</span></header>')
    a('<div class="wrap">')

    # TABS
    a('<div class="tabs">')
    a('<button class="tab on" onclick="showPanel(' + chr(39) + 'search' + chr(39) + ')">&#128269; Search</button>')
    a('<button class="tab"    onclick="showPanel(' + chr(39) + 'index'  + chr(39) + ')">&#128209; Index</button>')
    a('<button class="tab"    onclick="showPanel(' + chr(39) + 'export' + chr(39) + ')">&#128228; Export</button>')
    a('</div>')

    # ── SEARCH PANEL ─────────────────────────────────────────────────────────
    a('<div id="pnl-search" class="pnl on">')
    a('<div class="st">Dataset</div>')
    a('<div class="dsg">')
    for ds, ico, nm, sub in [
        ('plenarprotokoll','&#128220;','Plenary Records','plenarprotokoll'),
        ('drucksache',     '&#128196;','Parliamentary Papers','drucksache'),
        ('person',         '&#128100;','Members of Parliament','person (MdB)'),
        ('vorgang',        '&#9881;',  'Proceedings','vorgang'),
    ]:
        on = ' on' if ds == 'plenarprotokoll' else ''
        a('<div class="ds%s" onclick="setDs(%s%s%s,this)">'
          '<span class="dsi">%s</span><div class="dsn">%s</div>'
          '<div class="dss">%s</div></div>'
          % (on, chr(39), ds, chr(39), ico, nm, sub))
    a('</div>')

    a('<div class="card"><div class="row">')
    a('<div class="fld" style="flex:1;min-width:180px"><label>Keyword</label>')
    a('<input type="text" id="q" placeholder="es. Klimaschutz, Haushalt... (filtra nei titoli)"'
      ' onkeydown="if(event.key===\'Enter\')doSearch()"></div>')
    a('<div class="fld"><label>Legislative Term</label>')
    a('<select id="wp"><option value="">All</option>' + WPO + '</select></div>')
    a('<div class="fld"><label>Results</label>')
    a('<input type="number" id="num" value="10" min="5" max="50" style="width:62px"></div>')
    a('<div class="fld" style="justify-content:flex-end"><label>&nbsp;</label>')
    a('<button class="btn" id="search-btn" onclick="doSearch()">&#128269; Search</button></div>')
    a('<div class="fld" style="justify-content:flex-end"><label>&nbsp;</label>')
    a('<button class="btn btn2" onclick="resetSearch()">&#10005; Reset</button></div>')
    a('</div></div>')

    a('<div class="ib" id="ib">'
      '<span class="il">Dataset:</span><span class="iv" id="ib-ds">-</span>'
      '<span class="il">Total:</span><span class="iv" id="ib-tot">-</span>'
      '<span class="il">Page:</span><span class="iv" id="ib-pg">-</span>'
      '<span class="il">Query:</span><span class="iv" id="ib-q">-</span></div>')
    a('<div id="err"></div>')
    a('<div id="loading"><div class="spin"></div>'
      '<div style="color:var(--mu);font-size:13px">Loading...</div></div>')
    a('<div id="empty">No results found.</div>')
    a('<div id="results"></div>')
    a('<div class="pg" id="pagination"></div>')
    a('</div>') # /pnl-search

    # ── INDEX PANEL ───────────────────────────────────────────────────────────
    a('<div id="pnl-index" class="pnl">')
    a('<div class="st">Dataset overview</div>')
    a('<div class="sg">')
    for ico, lbl, sid, sub in [
        ('&#128220;','Plenary Records','sv-prot','since 1st term'),
        ('&#128196;','Drucksachen','sv-druck','parliamentary papers'),
        ('&#128100;','Members of Parliament (MdB)','sv-pers','since 1949'),
        ('&#9881;','Proceedings','sv-vorg','legislative procedures'),
    ]:
        a('<div class="sc"><div class="si">%s</div><div class="sl">%s</div>'
          '<div class="sv" id="%s">...</div><div class="ss">%s</div></div>'
          % (ico, lbl, sid, sub))
    a('</div>')

    for sid, ico, title, icnid, tabs_html, listid in [
        ('is-prot',  '&#128220;', 'Plenary Records',             'icn-prot',  PT,  'prot-list'),
        ('is-druck', '&#128196;', 'Parliamentary Papers',         'icn-druck', DT,  'druck-list'),
        ('is-vorg',  '&#9881;',   'Proceedings (Vorgange)',      'icn-vorg',  VT,  'vorg-list'),
    ]:
        op = ' op' if sid == 'is-prot' else ''
        tg = sid.replace('is-','') + '-tg'
        a('<div class="is%s" id="%s">' % (op, sid))
        a('<div class="ih" onclick="toggleSec(%s%s%s)">'
          '<span class="iit">%s</span><span class="itn">%s</span>'
          '<span class="icn" id="%s">-</span><span class="ich">&#9658;</span></div>'
          % (chr(39), sid, chr(39), ico, title, icnid))
        a('<div class="ibdy">')
        a('<div class="ifl"><span class="ifl-l">Legislative Term</span>'
          '<div class="wpts" id="%s">%s</div></div>' % (tg, tabs_html))
        a('<div id="%s"><div class="iload">'
          '<div class="mspin"></div> Loading...</div></div>' % listid)
        a('</div></div>')

    # Person A-Z section
    a('<div class="is" id="is-pers">')
    a('<div class="ih" onclick="toggleSec(\'is-pers\')">'
      '<span class="iit">&#128100;</span><span class="itn">Members of Parliament (MdB) - A-Z</span>'
      '<span class="icn" id="icn-pers">-</span><span class="ich">&#9658;</span></div>')
    a('<div class="ibdy">')
    a('<div class="ifl"><span class="ifl-l">Initial</span>'
      '<div class="ab" id="alpha-bar"></div></div>')
    a('<div id="pers-list"><div class="iempty">Click a letter.</div></div>')
    a('</div></div>')
    a('</div>') # /pnl-index

    # ── EXPORT PANEL ──────────────────────────────────────────────────────────
    a('<div id="pnl-export" class="pnl">')
    a('<div class="expw">')

    # Left: form
    a('<div class="expf">')
    a('<h2>&#128228; Export documenti</h2>')
    a('<p>Export Bundestag documents as TXT (for NotebookLM) or download original PDFs.</p>')

    # Subtabs
    a('<div class="exp-tabs">')
    a('<button class="exp-tab on" onclick="expTab(\'txt\',this)">&#128196; TXT File</button>')
    a('<button class="exp-tab"    onclick="expTab(\'pdf\',this)">&#128229; Download PDF</button>')
    a('</div>')

    # TXT sub-panel
    a('<div class="expsub on" id="sub-txt">')
    a('<div class="fld"><label>Dataset</label>')
    a('<select id="ex-ds">')
    a('<option value="plenarprotokoll">Plenary Records</option>')
    a('<option value="drucksache">Parliamentary Papers</option>')
    a('<option value="vorgang" selected>Proceedings</option>')
    a('</select></div>')
    a('<div class="row">')
    a('<div class="fld"><label>Data inizio</label>'
      '<input type="date" id="ex-from" value="2022-01-01"></div>')
    a('<div class="fld"><label>Data fine</label>'
      '<input type="date" id="ex-to" value="' + TODAY + '"></div>')
    a('</div>')
    a('<div class="fld"><label>Legislative Term (opt.)</label>')
    a('<select id="ex-wp"><option value="">All</option>' + WPO + '</select></div>')
    a('<div class="fld"><label>Keyword (opt.)</label>')
    a('<input type="text" id="ex-q" placeholder="es. Klimaschutz..."></div>')
    a('<div class="fld"><label>Max documents</label>')
    a('<select id="ex-max">'
      '<option value="100">100</option>'
      '<option value="250">250</option>'
      '<option value="500" selected>500</option>'
      '<option value="1000">1.000</option>'
      '<option value="0">Tutti</option>'
      '</select></div>')
    a('<button class="btn btng" id="ex-btn" onclick="startExport()">&#8659; Export TXT</button>')
    a('</div>') # /sub-txt

    # PDF sub-panel
    a('<div class="expsub" id="sub-pdf">')
    a('<p style="font-size:12px;color:#555">Download original PDFs from the Bundestag server.'
      ' I PDF sono disponibili per <strong>Parliamentary Papers</strong> e <strong>Plenary Records</strong>.</p>')
    a('<div class="fld"><label>Dataset</label>')
    a('<select id="pdf-ds">'
      '<option value="plenarprotokoll">Plenary Records</option>'
      '<option value="drucksache" selected>Parliamentary Papers</option>'
      '</select></div>')
    a('<div class="row">')
    a('<div class="fld"><label>Data inizio</label>'
      '<input type="date" id="pdf-from" value="2022-01-01"></div>')
    a('<div class="fld"><label>Data fine</label>'
      '<input type="date" id="pdf-to" value="' + TODAY + '"></div>')
    a('</div>')
    a('<div class="fld"><label>Legislative Term (opt.)</label>')
    a('<select id="pdf-wp"><option value="">All</option>' + WPO + '</select></div>')
    a('<div class="fld"><label>Keyword (opt.)</label>')
    a('<input type="text" id="pdf-q" placeholder="es. Klimaschutz..."></div>')
    a('<div class="fld"><label>Max PDFs</label>')
    a('<select id="pdf-max">'
      '<option value="10">10</option>'
      '<option value="25">25</option>'
      '<option value="50">50</option>'
      '<option value="100">100</option>'
      '<option value="200" selected>200</option>'
      '</select></div>')
    a('<div class="nlm">&#128161; I PDF vengono salvati in <em>bundestag_export/pdf/</em>. Max 200 PDF (~3-6 min a seconda della connessione).'
      ' Puoi poi importarli in NotebookLM: <strong>Aggiungi fonte &rarr; Carica file</strong>.</div>')
    a('<button class="btn btng" id="pdf-btn" onclick="startPdfDownload()">&#8659; Download PDFs</button>')
    a('</div>') # /sub-pdf
    a('</div>') # /expf

    # Right: progress + result
    a('<div class="expr">')
    a('<h2>&#128202; Status</h2>')
    a('<div class="pw"><div class="pb" id="pb"></div></div>')
    a('<div class="plog" id="plog">Waiting...</div>')
    a('<div class="eres" id="eres">')
    a('<h3>&#10003; Done!</h3>')
    a('<div class="einfo" id="einfo"></div>')
    a('</div>')
    a('</div>') # /expr
    a('</div>') # /expw
    a('</div>') # /pnl-export

    a('</div>') # /wrap
    a('<script>' + JS + '</script>')
    a('</body></html>')
    return '\n'.join(h)


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        if args and str(args[1]) not in ('200', '304'):
            print("  [%s] %s" % (args[1], args[0]))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path
        params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}

        if path in ('/', '/index.html'):
            body = build_html().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path.startswith('/api/'):
            ep = path[5:]
            params['apikey'] = API_KEY
            params['format'] = 'json'
            # Always restrict to Bundestag documents (exclude Bundesrat)
            if ep in ('drucksache', 'plenarprotokoll', 'vorgang',
                      'drucksache-text', 'plenarprotokoll-text'):
                params.setdefault('f.zuordnung', 'BT')
            url = DIP_BASE + '/' + ep + '?' + urllib.parse.urlencode(params)
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'BundestagExplorer/1.0'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                err = json.dumps({'error': str(e)}).encode()
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err)

        elif path == '/search':
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self._run_fulltext_search(params)

        elif path == '/export':
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            mode = params.get('mode', 'txt')
            if mode == 'pdf':
                self._run_pdf(params)
            else:
                self._run_txt(params)

        elif path == '/download':
            fname = os.path.basename(params.get('file', ''))
            fpath = os.path.join(EXPORT_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, 'rb') as fh:
                    data = fh.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="' + fname + '"')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404); self.end_headers()

        else:
            self.send_response(404); self.end_headers()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _emit(self, obj):
        try:
            line = (json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8')
            self.wfile.write(line); self.wfile.flush()
        except Exception:
            pass

    def _dip(self, ep, params):
        params['apikey'] = API_KEY
        params['format'] = 'json'
        url = DIP_BASE + '/' + ep + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent':'BundestagExplorer/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def _fetch_docs(self, params, max_docs):
        """Paginate DIP API and return list of documents."""
        docs = []; cursor = None; page = 0; total = None
        dataset = params.pop('dataset')
        # Always filter for Bundestag documents only (exclude Bundesrat)
        # f.zuordnung supported on: drucksache, plenarprotokoll, vorgang
        if dataset in ('drucksache', 'plenarprotokoll', 'vorgang',
                       'drucksache-text', 'plenarprotokoll-text'):
            params.setdefault('f.zuordnung', 'BT')
        while True:
            page += 1
            p = dict(params, num=100)
            if cursor: p['cursor'] = cursor
            data  = self._dip(dataset, p)
            if total is None:
                total = data.get('numFound', 0)
                self._emit({'type':'progress', 'text': str(total) + ' documenti found'})
            batch = data.get('documents') or []
            if not batch: break
            docs.extend(batch)
            self._emit({'type':'progress', 'pct': min(80, int(len(docs)/max(total,1)*80)),
                        'text': 'Page' + str(page) + ': ' + str(len(docs)) + ' doc...'})
            cursor = data.get('cursor')
            if not cursor: break
            if max_docs and len(docs) >= max_docs:
                docs = docs[:max_docs]; break
        return docs

    # ── TXT export ────────────────────────────────────────────────────────────
    def _run_txt(self, params):
        dataset = params.get('dataset', 'vorgang')
        dfrom   = params.get('date_from', '')
        dto     = params.get('date_to', datetime.date.today().isoformat())
        wp      = params.get('wp', '')
        query   = params.get('query', '')
        maxd    = int(params.get('max', 500))
        LABEL   = {'plenarprotokoll':'Plenary Records',
                   'drucksache':'Parliamentary Papers', 'vorgang':'Proceedings'}

        self._emit({'type':'progress', 'pct':0,
                    'text':'Starting TXT: ' + LABEL.get(dataset,dataset) + ' | ' + dfrom + ' -> ' + dto})
        p = {'dataset': dataset}
        if dfrom: p['f.datum.start'] = dfrom
        if dto:   p['f.datum.end']   = dto
        if wp:    p['f.wahlperiode'] = wp
        if query: p['f.suche']       = query

        try:
            docs = self._fetch_docs(p, maxd)
        except Exception as e:
            self._emit({'type':'error', 'text': str(e)}); return

        self._emit({'type':'progress', 'pct':85, 'text':'Generating TXT...'})
        hdr = '\n'.join([
            'BUNDESTAG OPENDATA EXPORT', '='*66,
            'Dataset:      ' + LABEL.get(dataset, dataset),
            'Period:       ' + dfrom + ' -> ' + dto,
            'Legislative Term:  ' + (wp + 'a Wahlperiode' if wp else 'All'),
            'Keyword:' + (' ' + query if query else ' -'),
            'Documents:    ' + str(len(docs)),
            'Generated:    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'Source:       https://search.dip.bundestag.de',
            '='*66, '',
            'NOTE FOR NOTEBOOKLM: each === block is one Bundestag document.', '', '',
        ])
        body_parts = []
        for i, doc in enumerate(docs):
            L = ['='*66, 'DOCUMENT #' + str(i+1), '='*66]
            title = doc.get('titel') or doc.get('betreff') or doc.get('dokumentnummer') or '(senza titolo)'
            L.append('TITLE:  ' + title)
            if doc.get('datum'):          L.append('DATE:   '  + doc['datum'][:10])
            if doc.get('wahlperiode'):    L.append('TERM:   '    + str(doc['wahlperiode']))
            if doc.get('dokumentnummer'): L.append('NUMBER: '+ doc['dokumentnummer'])
            if doc.get('drucksachetyp'):  L.append('TYPE:   '  + doc['drucksachetyp'])
            if doc.get('vorgangstyp'):    L.append('TYPE:   '  + doc['vorgangstyp'])
            au = doc.get('autoren_anzeige') or []
            if au: L.append('AUTHORS:' + ', '.join(au[:5]))
            fs = doc.get('fundstelle') or {}
            if fs.get('pdf_url'): L.append('PDF:    ' + fs['pdf_url'])
            if doc.get('id'):     L.append('DIP:    https://dip.bundestag.de/vorgang/x/' + doc['id'])
            L.append('')
            body = doc.get('abstract') or doc.get('beschreibung') or ''
            if body: L.append('CONTENT:\n' + body.strip())
            L.append('')
            body_parts.append('\n'.join(L))

        txt = hdr + '\n'.join(body_parts)
        sds   = re.sub(r'[^a-z0-9]', '_', dataset)
        fname = 'bundestag_' + sds + '_' + dfrom.replace('-','') + '_' + dto.replace('-','') + '.txt'
        fpath = os.path.join(EXPORT_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as fh:
            fh.write(txt)
        kb = os.path.getsize(fpath) / 1024
        sz = (str(round(kb, 1)) + ' KB') if kb < 1024 else (str(round(kb/1024, 2)) + ' MB')
        self._emit({'type':'progress', 'pct':100, 'text':'File: ' + fname + ' (' + sz + ')'})
        self._emit({'type':'done', 'filename':fname, 'count':len(docs), 'size':sz})

    # ── PDF download ──────────────────────────────────────────────────────────
    def _run_pdf(self, params):
        dataset = params.get('dataset', 'drucksache')
        dfrom   = params.get('date_from', '')
        dto     = params.get('date_to', datetime.date.today().isoformat())
        wp      = params.get('wp', '')
        query   = params.get('query', '')
        maxd    = min(int(params.get('max', 200)), 200)  # hard cap 200
        pdf_dir = os.path.join(EXPORT_DIR, 'pdf')
        os.makedirs(pdf_dir, exist_ok=True)

        self._emit({'type':'progress', 'pct':0,
                    'text':'PDF search: ' + dataset + ' | ' + dfrom + ' -> ' + dto})
        p = {'dataset': dataset}
        if dfrom: p['f.datum.start'] = dfrom
        if dto:   p['f.datum.end']   = dto
        if wp:    p['f.wahlperiode'] = wp
        if query: p['f.suche']       = query

        try:
            docs = self._fetch_docs(p, maxd)
        except Exception as e:
            self._emit({'type':'error', 'text': str(e)}); return

        # Build PDF URL list
        pdf_list = []
        for doc in docs:
            url = ''
            fs  = doc.get('fundstelle') or {}
            url = fs.get('pdf_url', '') or ''
            if not url:
                dnum = doc.get('dokumentnummer', '')
                if dnum and '/' in dnum:
                    parts = dnum.split('/')
                    if len(parts) == 2:
                        wp_s  = parts[0].zfill(2)
                        doc_s = parts[1].zfill(5)
                        url   = 'https://dserver.bundestag.de/btd/' + wp_s + '/' + doc_s[:3] + '/' + wp_s + doc_s + '.pdf'
            if url:
                num  = doc.get('dokumentnummer', 'doc')
                date = (doc.get('datum', '') or '')[:10].replace('-', '')
                safe = re.sub(r'[^a-zA-Z0-9_-]', '_', str(num))
                pdf_list.append((url, safe + '_' + date + '.pdf'))

        self._emit({'type':'progress', 'pct':10,
                    'text': str(len(pdf_list)) + ' PDF da scaricare (of ' + str(len(docs)) + ' docs)'})

        if not pdf_list:
            self._emit({'type':'error',
                        'text':'Nessun PDF trovato. Prova con Parliamentary Papers o Plenary Records.'}); return

        ok = 0; err = 0; total_bytes = 0
        for i, (url, fname) in enumerate(pdf_list):
            pct = 10 + int(((i+1) / len(pdf_list)) * 85)
            fpath = os.path.join(pdf_dir, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 500:
                ok += 1; total_bytes += os.path.getsize(fpath)
                self._emit({'type':'progress', 'pct':pct,
                            'text':'[%d/%d] already present: %s' % (i+1, len(pdf_list), fname)}); continue
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; BundestagExplorer/1.0)',
                    'Accept': 'application/pdf,*/*'})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                if len(data) < 100 or (b'<html' in data[:200].lower()):
                    raise ValueError('Response is not a PDF')
                with open(fpath, 'wb') as fh:
                    fh.write(data)
                ok += 1; total_bytes += len(data)
                self._emit({'type':'progress', 'pct':pct,
                            'text':'[%d/%d] OK: %s (%d KB)' % (i+1, len(pdf_list), fname, len(data)//1024)})
            except Exception as e:
                err += 1
                self._emit({'type':'progress', 'pct':pct,
                            'text':'[%d/%d] SKIP: %s - %s' % (i+1, len(pdf_list), fname, str(e)[:60])})
            time.sleep(0.3)

        kb = total_bytes / 1024
        sz = (str(round(kb,1)) + ' KB') if kb < 1024 else (str(round(kb/1024,2)) + ' MB')
        self._emit({'type':'progress', 'pct':100,
                    'text':'Completed: %d downloaded, %d skipped' % (ok, err)})
        self._emit({'type':'done', 'count':ok, 'folder':pdf_dir, 'size':sz})


    def _run_fulltext_search(self, params):
        """
        Full-text search using drucksache-text / plenarprotokoll-text endpoints.
        These return the full OCR text of each document.
        We paginate, filter server-side, and stream matching docs back.
        vorgang has no -text endpoint: we filter on titel+deskriptoren.
        """
        query   = params.get('q', '').strip().lower()
        dataset = params.get('dataset', 'drucksache')
        wp      = params.get('wp', '')
        dfrom   = params.get('date_from', '')
        dto     = params.get('date_to', '')
        num     = int(params.get('num', 20))   # how many MATCHES to find
        cursor  = params.get('cursor', '')

        if not query:
            self._emit({'type': 'error', 'text': 'Empty query'}); return

        # Map dataset to the right endpoint
        TEXT_EP = {
            'drucksache':      'drucksache-text',
            'plenarprotokoll': 'plenarprotokoll-text',
            'vorgang':         'vorgang',        # no -text, filter on metadata
        }
        ep = TEXT_EP.get(dataset, 'drucksache-text')

        # Base filter params — always filter Bundestag only
        base = {'f.zuordnung': 'BT'}
        if wp:    base['f.wahlperiode'] = wp
        if dfrom: base['f.datum.start'] = dfrom
        if dto:   base['f.datum.end']   = dto
        if cursor: base['cursor']       = cursor

        # Paginate until we have enough matches or exhaust the corpus
        # drucksache-text returns max 10 per page, others max 100
        page_size  = 10 if 'text' in ep else 100
        matches    = []
        scanned    = 0
        page       = 0
        next_cursor = None
        total_api  = None
        q_words    = [w for w in query.split() if w]

        self._emit({'type': 'progress', 'pct': 0,
                    'text': 'Full-text search: "%s" in %s...' % (query, dataset)})

        while len(matches) < num:
            page += 1
            p = dict(base, num=page_size)
            if next_cursor: p['cursor'] = next_cursor

            try:
                data = self._dip(ep, p)
            except Exception as e:
                self._emit({'type': 'error', 'text': 'API error page.%d: %s' % (page, e)})
                break

            if total_api is None:
                total_api = data.get('numFound', 0)
                self._emit({'type': 'progress', 'text':
                    '%d documents in corpus, scanning...' % total_api})

            docs = data.get('documents') or []
            if not docs: break

            for doc in docs:
                scanned += 1
                # Build searchable text
                if ep in ('drucksache-text', 'plenarprotokoll-text'):
                    haystack = (
                        (doc.get('titel')       or '') + ' ' +
                        (doc.get('text')        or '') + ' ' +
                        (doc.get('abstract')    or '')
                    ).lower()
                else:
                    # vorgang: titel + deskriptoren
                    desks = ' '.join(
                        d.get('name','') for d in (doc.get('deskriptor') or [])
                    )
                    haystack = (
                        (doc.get('titel')        or '') + ' ' +
                        (doc.get('betreff')      or '') + ' ' +
                        (doc.get('abstract')     or '') + ' ' +
                        desks
                    ).lower()

                # All words must appear (AND logic)
                if all(w in haystack for w in q_words):
                    # Strip huge text field before sending to browser
                    doc_out = {k: v for k,v in doc.items() if k != 'text'}
                    # Add snippet: 200 chars around first match
                    full_text = doc.get('text', '')
                    if full_text and q_words:
                        idx = full_text.lower().find(q_words[0])
                        if idx >= 0:
                            start = max(0, idx - 80)
                            end   = min(len(full_text), idx + 160)
                            snippet = ('...' if start > 0 else '') +                                       full_text[start:end].strip() +                                       ('...' if end < len(full_text) else '')
                            doc_out['snippet'] = snippet
                    matches.append(doc_out)

            pct = min(90, int(scanned / max(total_api, 1) * 90))
            self._emit({'type': 'progress', 'pct': pct,
                        'text': 'Page%d: scanned %d, found %d...' % (
                            page, scanned, len(matches))})

            next_cursor = data.get('cursor')
            if not next_cursor: break

        self._emit({
            'type': 'results',
            'documents': matches[:num],
            'numFound':  len(matches),
            'scanned':   scanned,
            'total':     total_api or 0,
            'cursor':    next_cursor or '',
            'query':     query,
        })


def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://localhost:' + str(PORT))

if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', PORT), Handler)
    print('=' * 50)
    print('  Bundestag OpenData Explorer')
    print('=' * 50)
    print('  URL:    http://localhost:' + str(PORT))
    print('  Export: ' + EXPORT_DIR)
    print('  Stop:   Ctrl+C')
    print('=' * 50)
    threading.Thread(target=open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.')
        server.server_close()
