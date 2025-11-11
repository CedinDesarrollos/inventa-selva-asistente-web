// BASE: viene del .env (en el server), pero el frontend pega al propio Flask que proxea a Railway.
// En este MVP, llamaremos directo a Railway desde el browser.
// Guard: si no hay jwt en sessionStorage, forzar /auth/login (excepto cuando ya estamos ahí)

(function(){
  const publicPaths = ['/auth/login'];
  if(!sessionStorage.getItem('jwt') && !publicPaths.includes(location.pathname)){
    // página de login simple servida desde Flask (puedes crear ruta /auth/login que renderice login.html)
    // Para simplificar, si no existe, redirigimos a /cases/ (que ya usa guard arriba)
  }
})();

const API_BASE = (document.querySelector('meta[name="api-base"]')?.content) || 
  'https://inventa-selva-asistente-production.up.railway.app';

function getAuthHeader(){
  const t = sessionStorage.getItem('jwt');
  return t ? {'Authorization': 'Bearer '+t} : {};
}

async function appPost(path, json){
  const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(json || {})});
  return r.json();
}

// Llamadas directas a Railway para endpoints específicos (cuando no querés pasar por blueprint)
async function appPostRaw(apiPath, json){
  const r = await fetch(API_BASE + apiPath, {
    method: 'POST',
    headers: { 'Content-Type':'application/json', ...getAuthHeader() },
    body: JSON.stringify(json || {})
  });
  if(!r.ok){ toast('Error '+r.status); }
  return r.json();
}

function toast(msg){
  const el = document.querySelector('#app-toast');
  el.querySelector('.toast-body').textContent = msg;
  const t = new bootstrap.Toast(el);
  t.show();
}

document.getElementById('btn-logout')?.addEventListener('click', ()=>{
  sessionStorage.removeItem('jwt');
  document.cookie = "jwt=; Max-Age=0; path=/";
  location.href = "/auth/login";
});
