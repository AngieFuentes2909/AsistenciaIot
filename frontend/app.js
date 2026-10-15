// ============================================================
//  CONTROL DE ASISTENCIA IOT - LÓGICA JAVASCRIPT
// ============================================================

const API_BASE = (window.location.protocol === 'file:') 
  ? 'http://127.0.0.1:8000' 
  : window.location.origin;

let asistenciasData = [];
let autoRefreshTimer = null;

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
  iniciarReloj();
  cargarKPIs();
  cargarAsistencias();
  cargarUsuarios();
  configurarTabs();
  configurarEventos();
});

// --- RELOJ DIGITAL EN VIVO ---
function iniciarReloj() {
  const clockEl = document.getElementById('live-clock');
  function actualizar() {
    const ahora = new Date();
    clockEl.textContent = ahora.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    });
  }
  actualizar();
  setInterval(actualizar, 1000);
}

// --- TABS DE NAVEGACIÓN ---
function configurarTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      cambiarTab(tabId);
    });
  });
}

function cambiarTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

  const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
  const activePanel = document.getElementById(tabId);

  if (activeBtn) activeBtn.classList.add('active');
  if (activePanel) activePanel.classList.add('active');

  if (tabId === 'tab-usuarios') cargarUsuarios();
  if (tabId === 'tab-asistencias') cargarAsistencias();
}

// --- CARGAR KPIS ---
async function cargarKPIs() {
  try {
    const res = await fetch(`${API_BASE}/api/asistencias/resumen`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('kpi-total').textContent = data.total_registros_hoy || 0;
      document.getElementById('kpi-entradas').textContent = data.entradas_hoy || 0;
      document.getElementById('kpi-salidas').textContent = data.salidas_hoy || 0;
    }

    const resUsers = await fetch(`${API_BASE}/api/usuarios/`);
    if (resUsers.ok) {
      const users = await resUsers.json();
      document.getElementById('kpi-usuarios').textContent = users.length || 0;
    }
  } catch (err) {
    console.warn('Error al cargar métricas:', err);
  }
}

// --- CARGAR ASISTENCIAS EN VIVO ---
async function cargarAsistencias() {
  const tbody = document.getElementById('asistencias-table-body');
  try {
    const res = await fetch(`${API_BASE}/api/asistencias/recientes?limit=30`);
    if (!res.ok) throw new Error('Error al conectar con la API');

    asistenciasData = await res.json();
    renderAsistencias(asistenciasData);
    cargarKPIs();
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color:#f43f5e; padding:20px;">
          ⚠️ No se pudo conectar al servidor FastAPI (${API_BASE}). Asegúrate de que uvicorn esté corriendo.
        </td>
      </tr>
    `;
  }
}

function renderAsistencias(lista) {
  const tbody = document.getElementById('asistencias-table-body');
  const filtro = (document.getElementById('search-input')?.value || '').toLowerCase().trim();

  const filtrados = lista.filter(item => 
    item.usuario_nombre.toLowerCase().includes(filtro) ||
    item.metodo.toLowerCase().includes(filtro) ||
    item.tipo.toLowerCase().includes(filtro)
  );

  if (filtrados.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color:var(--text-muted); padding:24px;">
          No hay registros coincidentes.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtrados.map(item => {
    const inicial = item.usuario_nombre.charAt(0).toUpperCase();
    const esEntrada = item.tipo.toUpperCase() === 'ENTRADA';
    const esRfid = item.metodo.toUpperCase() === 'RFID';
    const fecha = new Date(item.timestamp);
    const fechaStr = fecha.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
    const horaStr = fecha.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });

    return `
      <tr>
        <td style="color:var(--text-sub); font-family:monospace;">#${item.id}</td>
        <td>
          <div class="user-cell">
            <div class="user-avatar">${inicial}</div>
            <div>
              <div style="font-weight:600;">${item.usuario_nombre}</div>
              <div style="font-size:0.75rem; color:var(--text-muted);">ID Usuario: ${item.usuario_id}</div>
            </div>
          </div>
        </td>
        <td>
          <span class="badge ${esRfid ? 'badge-rfid' : 'badge-teclado'}">
            ${esRfid ? '💳 RFID' : '⌨️ TECLADO'}
          </span>
        </td>
        <td>
          <span class="badge ${esEntrada ? 'badge-entrada' : 'badge-salida'}">
            ${esEntrada ? '⬇️ ENTRADA' : '⬆️ SALIDA'}
          </span>
        </td>
        <td>
          <span class="time-stamp">${fechaStr} - ${horaStr}</span>
        </td>
        <td style="color:var(--text-muted); font-size:0.8rem;">
          ${item.dispositivo_id || 'ESP32_MAIN'}
        </td>
      </tr>
    `;
  }).join('');
}

// --- CARGAR USUARIOS ---
async function cargarUsuarios() {
  const tbody = document.getElementById('usuarios-table-body');
  try {
    const res = await fetch(`${API_BASE}/api/usuarios/`);
    if (!res.ok) throw new Error('Error al cargar usuarios');

    const usuarios = await res.json();
    if (usuarios.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px;">No hay usuarios registrados.</td></tr>`;
      return;
    }

    tbody.innerHTML = usuarios.map(u => {
      const inicial = u.nombre.charAt(0).toUpperCase();
      return `
        <tr>
          <td>
            <div class="user-cell">
              <div class="user-avatar" style="background:rgba(59,130,246,0.15); color:#60a5fa;">${inicial}</div>
              <div style="font-weight:600;">${u.nombre}</div>
            </div>
          </td>
          <td style="font-family:monospace; font-weight:600;">${u.documento}</td>
          <td>
            ${u.rfid_uid 
              ? `<span class="badge badge-rfid">${u.rfid_uid}</span>` 
              : `<span style="color:var(--text-sub); font-size:0.8rem;">Sin tarjeta</span>`}
          </td>
          <td style="font-family:monospace; color:var(--text-muted);">
            ${u.pin ? '••••' : '<span style="color:var(--text-sub); font-size:0.8rem;">Sin PIN</span>'}
          </td>
          <td>${u.departamento || 'General'}</td>
          <td>
            <span class="badge" style="background:rgba(16,185,129,0.1); color:#34d399;">
              ● Activo
            </span>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#f43f5e; padding:20px;">Error al cargar lista de usuarios.</td></tr>`;
  }
}

// --- CONFIGURAR EVENTOS ---
function configurarEventos() {
  // Búsqueda en vivo
  document.getElementById('search-input')?.addEventListener('input', () => {
    renderAsistencias(asistenciasData);
  });

  // Botón manual de refrescar
  document.getElementById('btn-refresh')?.addEventListener('click', () => {
    cargarAsistencias();
    mostrarToast('Asistencias actualizadas', 'success');
  });

  // Auto refresco
  const autoCheckbox = document.getElementById('auto-refresh');
  function toggleTimer() {
    if (autoCheckbox.checked) {
      if (!autoRefreshTimer) {
        autoRefreshTimer = setInterval(cargarAsistencias, 3000);
      }
    } else {
      clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
  }
  autoCheckbox?.addEventListener('change', toggleTimer);
  toggleTimer();

  // Formulario nuevo usuario
  const formUser = document.getElementById('form-nuevo-usuario');
  formUser?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const nombre = document.getElementById('u-nombre').value.trim();
    const documento = document.getElementById('u-documento').value.trim();
    const rfid = document.getElementById('u-rfid').value.trim().toUpperCase() || null;
    const pin = document.getElementById('u-pin').value.trim() || null;
    const departamento = document.getElementById('u-departamento').value.trim() || 'General';

    try {
      const res = await fetch(`${API_BASE}/api/usuarios/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, documento, rfid_uid: rfid, pin, departamento })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Error al guardar usuario');
      }

      mostrarToast(`Usuario ${nombre} creado con éxito`, 'success');
      formUser.reset();
      cargarKPIs();
      cambiarTab('tab-usuarios');
    } catch (err) {
      mostrarToast(err.message, 'error');
    }
  });

  // Simulador de Asistencia Web
  const btnSimular = document.getElementById('btn-simular');
  const simResultado = document.getElementById('sim-resultado');

  btnSimular?.addEventListener('click', async () => {
    const metodo = document.getElementById('sim-metodo').value;
    const identificador = document.getElementById('sim-identificador').value.trim();
    const tipo = document.getElementById('sim-tipo').value;

    if (!identificador) {
      mostrarToast('Por favor ingresa un identificador', 'error');
      return;
    }

    try {
      btnSimular.disabled = true;
      btnSimular.textContent = 'Enviando...';

      const res = await fetch(`${API_BASE}/api/asistencias/registrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metodo, identificador, tipo })
      });

      const data = await res.json();
      simResultado.style.display = 'block';

      if (data.acceso) {
        simResultado.innerHTML = `
          <div style="background:rgba(16,185,129,0.12); border:1px solid #10b981; border-radius:12px; padding:16px;">
            <div style="font-weight:700; color:#34d399; font-size:1.05rem;">✅ ${data.mensaje}</div>
            <div style="margin-top:6px; color:#cbd5e1; font-size:0.9rem;">
              <strong>Empleado:</strong> ${data.usuario_nombre} &nbsp;|&nbsp; 
              <strong>Tipo:</strong> ${data.tipo} &nbsp;|&nbsp; 
              <strong>Método:</strong> ${data.metodo}
            </div>
            <div style="margin-top:4px; color:#94a3b8; font-size:0.8rem;">
              Mensaje LCD: "${data.mensaje_lcd1} / ${data.mensaje_lcd2}"
            </div>
          </div>
        `;
        mostrarToast(`Asistencia de ${data.usuario_nombre} registrada (${data.tipo})`, 'success');
        cargarAsistencias();
      } else {
        simResultado.innerHTML = `
          <div style="background:rgba(244,63,94,0.12); border:1px solid #f43f5e; border-radius:12px; padding:16px;">
            <div style="font-weight:700; color:#fb7185; font-size:1.05rem;">❌ ${data.mensaje}</div>
            <div style="margin-top:6px; color:#cbd5e1; font-size:0.9rem;">Identificador no encontrado en la base de datos.</div>
          </div>
        `;
        mostrarToast(data.mensaje, 'error');
      }
    } catch (err) {
      mostrarToast('Error de conexión con el backend', 'error');
    } finally {
      btnSimular.disabled = false;
      btnSimular.textContent = '⚡ Enviar Registro Simulado';
    }
  });
}

// --- NOTIFICACIONES TOAST ---
function mostrarToast(mensaje, tipo = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = (tipo === 'success' ? '✅ ' : '❌ ') + mensaje;
  toast.className = `toast toast-${tipo} show`;

  setTimeout(() => {
    toast.className = 'toast';
  }, 3500);
}
