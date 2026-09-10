
// ---------- global helpers ----------
function showToast(msg){
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(function(){ t.classList.remove('show'); }, 2600);
}

function wireSearch(inputId, tbodyId){
  var input = document.getElementById(inputId);
  var tbody = document.getElementById(tbodyId);
  if(!input || !tbody) return;
  input.addEventListener('input', function(){
    var q = this.value.toLowerCase();
    tbody.querySelectorAll('tr').forEach(function(tr){
      tr.style.display = tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
    });
  });
}

function wireFilter(selectId, tbodyId, colIndex){
  var select = document.getElementById(selectId);
  var tbody = document.getElementById(tbodyId);
  if(!select || !tbody) return;
  select.addEventListener('change', function(){
    var v = this.value;
    tbody.querySelectorAll('tr').forEach(function(tr){
      if(v === 'All'){ tr.style.display = ''; return; }
      var cell = tr.children[colIndex];
      tr.style.display = (cell && cell.textContent.trim() === v) ? '' : 'none';
    });
  });
}

function goToPage(id){
  var navLink = document.querySelector('.side-nav [data-page="'+id+'"]');
  if(!navLink) return;
  navLink.click();
}

function openDetail(title, bodyHtml){
  document.getElementById('detail-title').textContent = title;
  document.getElementById('detail-body').innerHTML = bodyHtml;
  document.getElementById('detail-overlay').classList.add('open');
}
document.addEventListener('DOMContentLoaded', function(){
  var d = document.getElementById('detail-overlay');
  document.getElementById('detail-close').addEventListener('click', function(){ d.classList.remove('open'); });
  document.getElementById('detail-dismiss').addEventListener('click', function(){ d.classList.remove('open'); });
  d.addEventListener('click', function(e){ if(e.target===d) d.classList.remove('open'); });
});

// Delegated click handling for simple row actions across every page
document.addEventListener('click', function(e){
  var btn = e.target.closest('[data-action]');
  if(!btn) return;
  var action = btn.dataset.action;
  var tr = btn.closest('tr');

  if(action === 'toggle-pill'){
    var pill = tr.querySelector('.pill');
    var curLabel = pill.textContent;
    var curClass = pill.className;
    pill.textContent = btn.dataset.label;
    pill.className = 'pill ' + btn.dataset.class;
    btn.dataset.label = curLabel;
    btn.dataset.class = curClass.replace('pill ', '');
    btn.textContent = btn.dataset.altText || btn.textContent;
    showToast(btn.dataset.toast || 'Status updated');
  }

  if(action === 'remove-row'){
    tr.style.opacity = '0';
    setTimeout(function(){ tr.remove(); }, 150);
    showToast(btn.dataset.toast || 'Removed');
  }

  if(action === 'print'){
    window.print();
  }

  if(action === 'toast'){
    showToast(btn.dataset.toast || 'Done');
  }
});

// ---------- sacks ----------
function drawSacks(id, count, maxGlyphs){
  var el = document.getElementById(id);
  if(!el) return;
  el.innerHTML = '';
  var per = Math.max(1, Math.round(count / maxGlyphs));
  var n = Math.min(maxGlyphs, Math.ceil(count / per));
  var frag = document.createDocumentFragment();
  for(var i=0;i<n;i++){
    var svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('class','sack');
    svg.setAttribute('viewBox','0 0 9 12');
    var path = document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d','M1.5 3 Q0 3 0 5 L0 10.5 Q0 12 1.8 12 L7.2 12 Q9 12 9 10.5 L9 5 Q9 3 7.5 3 Z');
    path.setAttribute('fill','#3FA35C');
    var tie = document.createElementNS('http://www.w3.org/2000/svg','path');
    tie.setAttribute('d','M2.8 0 L6.2 0 L5.2 3 L3.8 3 Z');
    tie.setAttribute('fill','#171A18');
    svg.appendChild(path);
    svg.appendChild(tie);
    frag.appendChild(svg);
  }
  el.appendChild(frag);
}
drawSacks('sacks-compd-dash', 640, 40);
drawSacks('sacks-urea-dash', 210, 40);
drawSacks('sacks-green-dash', 95, 40);
drawSacks('sacks-compd-wh', 640, 40);
drawSacks('sacks-urea-wh', 210, 40);
drawSacks('sacks-green-wh', 95, 40);
drawSacks('sacks-client', 8, 40);

// ---------- Dashboard ----------
document.getElementById('dash-refresh').addEventListener('click', function(){
  document.getElementById('dash-updated').textContent = 'Last updated: just now';
  showToast('Dashboard refreshed');
});
document.getElementById('dash-range').addEventListener('change', function(){
  document.getElementById('dash-range-label').textContent = this.value.toLowerCase();
  showToast('Showing figures for ' + this.value.toLowerCase());
});

// ---------- Shops ----------
wireSearch('shops-search', 'shops-body');
function applyShopFilters(){
  var prov = document.getElementById('shops-filter-province').value;
  var stat = document.getElementById('shops-filter-status').value;
  document.getElementById('shops-body').querySelectorAll('tr').forEach(function(tr){
    var okProv = (prov === 'All') || (tr.dataset.province === prov);
    var pill = tr.querySelector('.pill');
    var okStat = (stat === 'All') || (pill && pill.textContent === stat);
    tr.style.display = (okProv && okStat) ? '' : 'none';
  });
}
document.getElementById('shops-filter-province').addEventListener('change', applyShopFilters);
document.getElementById('shops-filter-status').addEventListener('change', applyShopFilters);

document.querySelectorAll('#shops-body .shop-clickable').forEach(function(cell){
  cell.addEventListener('click', function(){
    var tr = cell.closest('tr');
    var name = tr.querySelector('.row-title').textContent;
    var loc = tr.querySelector('.row-sub').textContent;
    var agent = tr.children[1].textContent;
    var portfolio = tr.children[2].textContent;
    var overdue = tr.children[3].textContent;
    var status = tr.querySelector('.pill').outerHTML;
    openDetail(name,
      '<div class="profile-meta" style="margin-bottom:14px;">' + loc + ' · Agent: ' + agent + '</div>' +
      '<div class="asset-line"><span>Portfolio value</span><b class="mono">' + portfolio + '</b></div>' +
      '<div class="asset-line"><span>Loans overdue</span><b class="mono">' + overdue + '</b></div>' +
      '<div class="asset-line" style="border-bottom:none;"><span>Status</span><span>' + status + '</span></div>'
    );
  });
});

(function(){
  var overlay = document.getElementById('add-shop-overlay');
  document.getElementById('add-shop-btn').addEventListener('click', function(){ overlay.classList.add('open'); });
  document.getElementById('add-shop-close').addEventListener('click', function(){ overlay.classList.remove('open'); });
  document.getElementById('add-shop-cancel').addEventListener('click', function(){ overlay.classList.remove('open'); });
  overlay.addEventListener('click', function(e){ if(e.target===overlay) overlay.classList.remove('open'); });
  document.getElementById('add-shop-save').addEventListener('click', function(){
    var name = document.getElementById('sh-name').value.trim();
    var errEl = document.getElementById('sh-error');
    if(!name){ errEl.classList.add('show'); return; }
    errEl.classList.remove('show');
    var province = document.getElementById('sh-province').value;
    var district = document.getElementById('sh-district').value.trim() || '—';
    var village = document.getElementById('sh-village').value.trim() || '—';
    var agent = document.getElementById('sh-agent').value.trim() || '—';
    var row = document.createElement('tr');
    row.dataset.province = province;
    row.innerHTML =
      '<td class="shop-clickable" style="cursor:pointer;"><div class="row-title">' + name + '</div><div class="row-sub">' + province + ' · ' + district + ' · ' + village + '</div></td>' +
      '<td>' + agent + '</td><td class="num mono">K 0</td><td class="num mono">0</td>' +
      '<td><span class="pill pill-ok">Healthy</span></td>' +
      '<td><button class="btn" data-action="toggle-pill" data-label="Suspended" data-class="pill-risk" data-alt-text="Reactivate" data-toast="Shop suspended">Suspend</button></td>';
    document.getElementById('shops-body').appendChild(row);
    row.querySelector('.shop-clickable').addEventListener('click', function(){
      openDetail(name, '<div class="profile-meta" style="margin-bottom:14px;">' + province + ' · ' + district + ' · ' + village + ' · Agent: ' + agent + '</div><div class="asset-line" style="border-bottom:none;"><span>Newly registered shop — no loan activity yet.</span></div>');
    });
    var stat = document.getElementById('shop-count-stat');
    stat.textContent = parseInt(stat.textContent,10) + 1;
    overlay.classList.remove('open');
    showToast('Shop added: ' + name);
  });
})();

document.querySelectorAll('[data-page]').forEach(function(link){
  link.addEventListener('click', function(e){
    e.preventDefault();
    var target = this.dataset.page;
    document.querySelectorAll('.side-link').forEach(function(l){ l.classList.remove('active'); });
    var navLink = document.querySelector('.side-nav [data-page="'+target+'"]');
    if(navLink) navLink.classList.add('active');
    document.querySelectorAll('.page').forEach(function(p){ p.classList.remove('active'); });
    var page = document.getElementById('page-'+target);
    if(page) page.classList.add('active');
    if(navLink) document.getElementById('page-title-text').textContent = navLink.textContent;
    window.scrollTo(0,0);
  });
});

document.getElementById('theme-toggle').addEventListener('click', function(){
  var isLight = document.body.classList.toggle('light');
  this.textContent = isLight ? 'Dark mode' : 'Light mode';
});

(function(){
  var overlay = document.getElementById('add-product-overlay');
  var openBtn = document.getElementById('add-product-btn');
  var closeBtn = document.getElementById('add-product-close');
  var cancelBtn = document.getElementById('add-product-cancel');
  var saveBtn = document.getElementById('add-product-save');
  var errorEl = document.getElementById('ap-error');
  var nameInput = document.getElementById('ap-name');
  var catInput = document.getElementById('ap-category');
  var unitInput = document.getElementById('ap-unit');
  var stockInput = document.getElementById('ap-stock');
  var priceInput = document.getElementById('ap-price');
  var tbody = document.getElementById('products-catalog-body');
  var countStat = document.getElementById('product-count-stat');
  var fertStat = document.getElementById('fert-count-stat');
  var assetStat = document.getElementById('asset-count-stat');

  function openModal(){
    overlay.classList.add('open');
    errorEl.classList.remove('show');
    nameInput.value = '';
    catInput.value = 'Fertilizer';
    unitInput.value = '';
    stockInput.value = '';
    priceInput.value = '';
    nameInput.focus();
  }
  function closeModal(){ overlay.classList.remove('open'); }

  openBtn.addEventListener('click', openModal);
  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', function(e){ if(e.target === overlay) closeModal(); });

  saveBtn.addEventListener('click', function(){
    var name = nameInput.value.trim();
    if(!name){
      errorEl.classList.add('show');
      nameInput.focus();
      return;
    }
    var category = catInput.value;
    var unit = unitInput.value.trim() || (category === 'Fertilizer' ? 'bags' : 'units');
    var stock = stockInput.value.trim() || '0';
    var price = priceInput.value.trim() || '—';

    var row = document.createElement('tr');
    row.setAttribute('data-cat', category);
    row.innerHTML =
      '<td class="row-title">' + name + '</td>' +
      '<td>' + category + '</td>' +
      '<td>' + unit + '</td>' +
      '<td class="num mono">' + stock + '</td>' +
      '<td class="num mono">' + price + '</td>';
    tbody.appendChild(row);

    countStat.textContent = tbody.querySelectorAll('tr').length;
    fertStat.textContent = tbody.querySelectorAll('tr[data-cat="Fertilizer"]').length;
    assetStat.textContent = tbody.querySelectorAll('tr[data-cat="Vehicle"], tr[data-cat="Equipment"]').length;

    closeModal();
  });
})();

(function(){
  var stockElMap = {
    'Comp D': {count:'stock-count-compd', sacks:'sacks-compd-wh'},
    'Urea': {count:'stock-count-urea', sacks:'sacks-urea-wh'},
    'Green Sulf': {count:'stock-count-green', sacks:'sacks-green-wh'}
  };
  var assetElMap = {
    'Tractor': 'asset-count-tractor',
    'Ox plough': 'asset-count-oxplough',
    'Water pump': 'asset-count-waterpump',
    'Grinding mill': 'asset-count-grindingmill'
  };

  function getStock(product){
    if(stockElMap[product]){
      return parseInt(document.getElementById(stockElMap[product].count).textContent, 10) || 0;
    }
    if(assetElMap[product]){
      return parseInt(document.getElementById(assetElMap[product]).textContent, 10) || 0;
    }
    return null;
  }
  function setStock(product, value){
    if(stockElMap[product]){
      document.getElementById(stockElMap[product].count).textContent = value;
      drawSacks(stockElMap[product].sacks, value, 40);
      var total = 0;
      Object.keys(stockElMap).forEach(function(p){ total += getStock(p); });
      document.getElementById('wh-total-bags').textContent = total;
    } else if(assetElMap[product]){
      document.getElementById(assetElMap[product]).textContent = value;
    }
  }
  function bumpStat(id){
    var el = document.getElementById(id);
    el.textContent = (parseInt(el.textContent,10) || 0) + 1;
  }

  // Receive stock
  var rsOverlay = document.getElementById('receive-stock-overlay');
  var rsBtn = document.getElementById('receive-stock-btn');
  var rsClose = document.getElementById('receive-stock-close');
  var rsCancel = document.getElementById('receive-stock-cancel');
  var rsSave = document.getElementById('receive-stock-save');
  var rsError = document.getElementById('rs-error');
  var rsProduct = document.getElementById('rs-product');
  var rsQty = document.getElementById('rs-qty');
  var rsSupplier = document.getElementById('rs-supplier');
  var rsBatch = document.getElementById('rs-batch');
  var incomingBody = document.getElementById('incoming-stock-body');

  function openRS(){ rsOverlay.classList.add('open'); rsError.classList.remove('show'); rsQty.value=''; rsSupplier.value=''; rsBatch.value=''; }
  function closeRS(){ rsOverlay.classList.remove('open'); }
  rsBtn.addEventListener('click', openRS);
  rsClose.addEventListener('click', closeRS);
  rsCancel.addEventListener('click', closeRS);
  rsOverlay.addEventListener('click', function(e){ if(e.target===rsOverlay) closeRS(); });

  rsSave.addEventListener('click', function(){
    var qty = parseInt(rsQty.value, 10);
    if(!qty || qty <= 0){ rsError.classList.add('show'); rsQty.focus(); return; }
    var product = rsProduct.value;
    var supplier = rsSupplier.value.trim() || '—';
    var batch = rsBatch.value.trim() || '—';

    var row = document.createElement('tr');
    row.innerHTML =
      '<td class="mono">Today</td><td>' + supplier + '</td><td>' + product + '</td>' +
      '<td class="num mono">' + qty + '</td><td>' + batch + '</td>' +
      '<td><span class="pill pill-ok">Received</span></td>';
    incomingBody.insertBefore(row, incomingBody.firstChild);

    var current = getStock(product);
    if(current !== null) setStock(product, current + qty);
    bumpStat('wh-incoming-count');
    closeRS();
  });

  // Assign stock to shop
  var asOverlay = document.getElementById('assign-stock-overlay');
  var asBtn = document.getElementById('assign-stock-btn');
  var asClose = document.getElementById('assign-stock-close');
  var asCancel = document.getElementById('assign-stock-cancel');
  var asSave = document.getElementById('assign-stock-save');
  var asError = document.getElementById('as-error');
  var asProduct = document.getElementById('as-product');
  var asQty = document.getElementById('as-qty');
  var asShop = document.getElementById('as-shop');
  var allocationBody = document.getElementById('allocation-body');

  function openAS(){ asOverlay.classList.add('open'); asError.classList.remove('show'); asQty.value=''; }
  function closeAS(){ asOverlay.classList.remove('open'); }
  asBtn.addEventListener('click', openAS);
  asClose.addEventListener('click', closeAS);
  asCancel.addEventListener('click', closeAS);
  asOverlay.addEventListener('click', function(e){ if(e.target===asOverlay) closeAS(); });

  asSave.addEventListener('click', function(){
    var qty = parseInt(asQty.value, 10);
    var product = asProduct.value;
    var current = getStock(product);
    if(!qty || qty <= 0 || (current !== null && qty > current)){
      asError.classList.add('show'); asQty.focus(); return;
    }
    var shop = asShop.value;

    var row = document.createElement('tr');
    row.innerHTML =
      '<td class="mono">Today</td><td>' + product + '</td>' +
      '<td class="num mono">' + qty + '</td><td>' + shop + '</td>' +
      '<td><span class="pill pill-ok">Dispatched</span></td>';
    allocationBody.insertBefore(row, allocationBody.firstChild);

    if(current !== null) setStock(product, current - qty);
    bumpStat('wh-allocated-count');
    closeAS();
  });
})();

(function(){
  var overlay = document.getElementById('transfer-stock-overlay');
  var btn = document.getElementById('transfer-stock-btn');
  var closeBtn = document.getElementById('transfer-stock-close');
  var cancelBtn = document.getElementById('transfer-stock-cancel');
  var saveBtn = document.getElementById('transfer-stock-save');
  var errEl = document.getElementById('ts-error');
  var qtyInput = document.getElementById('ts-qty');
  var tbody = document.getElementById('transfer-body');

  function open(){ overlay.classList.add('open'); errEl.classList.remove('show'); qtyInput.value=''; }
  function close(){ overlay.classList.remove('open'); }
  btn.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  cancelBtn.addEventListener('click', close);
  overlay.addEventListener('click', function(e){ if(e.target===overlay) close(); });

  saveBtn.addEventListener('click', function(){
    var qty = parseInt(qtyInput.value, 10);
    if(!qty || qty <= 0){ errEl.classList.add('show'); return; }
    var product = document.getElementById('ts-product').value;
    var from = document.getElementById('ts-from').value;
    var to = document.getElementById('ts-to').value;
    if(from === to){ errEl.textContent = 'From and to shops must be different.'; errEl.classList.add('show'); return; }
    var row = document.createElement('tr');
    row.innerHTML = '<td class="mono">Today</td><td>' + product + '</td><td class="num mono">' + qty + '</td><td>' + from + '</td><td>' + to + '</td><td><span class="pill pill-ok">Completed</span></td>';
    tbody.insertBefore(row, tbody.firstChild);
    close();
    showToast('Transferred ' + qty + ' ' + product + ' to ' + to);
  });
})();

document.getElementById('save-thresholds-btn').addEventListener('click', function(){
  showToast('Reorder thresholds saved');
});

