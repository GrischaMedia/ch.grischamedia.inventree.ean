(function(){
  function getCookie(name){
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if(parts.length === 2) return parts.pop().split(';').shift();
  }

  const statusEl = () => document.getElementById('gm-ean-status');
  const inputEl = () => document.getElementById('gm-ean-input');

  async function save(){
    const ean = (inputEl().value || '').trim();
    statusEl().className = '';
    statusEl().textContent = '';

    const fd = new FormData();
    fd.append('ean', ean);

    const resp = await fetch(gmEAN.setUrl, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken') || getCookie('csrf') || ''
      },
      body: fd
    });

    let data = {};
    try { data = await resp.json(); } catch(e){}

    if(!resp.ok || !data.success){
      statusEl().className = 'text-danger';
      statusEl().textContent = (data && data.error) ? data.error : 'Fehler beim Speichern';
      return;
    }

    statusEl().className = 'text-success';
    statusEl().textContent = 'Gespeichert';
    gmEAN.current = ean;
  }

  function clear(){
    inputEl().value = '';
    statusEl().className = '';
    statusEl().textContent = '';
  }

  window.gmEAN = window.gmEAN || {};
  gmEAN.save = save;
  gmEAN.clear = clear;
})();