/* WDC App — Frontend API helper
   Tiny wrapper around fetch() that handles auth token, JSON, errors, toasts.
*/
const API = (() => {
  const TOKEN_KEY = 'wdc_token';
  const USER_KEY = 'wdc_user';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || getCookie('token');
  }
  function setToken(token, user) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
  function getUser() {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); }
    catch { return null; }
  }
  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  async function request(method, url, body) {
    const opts = {
      method,
      headers: {},
      credentials: 'include',
    };
    const token = getToken();
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    let data = null;
    try { data = await res.json(); } catch {}
    if (!res.ok) {
      const msg = (data && data.detail) || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  }

  return {
    getToken, setToken, clearToken, getUser,
    get:  (u) => request('GET', u),
    post: (u, b) => request('POST', u, b),
    patch:(u, b) => request('PATCH', u, b),
    del:  (u) => request('DELETE', u),

    signup: (b) => request('POST', '/api/auth/signup', b),
    studentLogin: (b) => request('POST', '/api/auth/login', b),
    adminLogin: (b) => request('POST', '/api/auth/admin/login', b),
    logout: () => request('POST', '/api/auth/logout'),
    me: () => request('GET', '/api/auth/me'),

    // public
    listEvents: () => request('GET', '/api/events'),
    getEvent: (id) => request('GET', '/api/events/' + id),
    listWomenDates: () => request('GET', '/api/women-dates'),

    // student
    myEvents: () => request('GET', '/api/me/events'),
    register: (id) => request('POST', `/api/me/events/${id}/register`),
    cancelReg: (id) => request('DELETE', `/api/me/events/${id}/register`),
    myAttendance: () => request('GET', '/api/me/attendance'),
    myNotifications: () => request('GET', '/api/me/notifications'),
    markNotifRead: (id) => request('POST', `/api/me/notifications/${id}/read`),

    // admin
    adminEvents: () => request('GET', '/api/admin/events'),
    createEvent: (b) => request('POST', '/api/admin/events', b),
    updateEvent: (id, b) => request('PATCH', `/api/admin/events/${id}`, b),
    deleteEvent: (id) => request('DELETE', `/api/admin/events/${id}`),
    participants: (id) => request('GET', `/api/admin/events/${id}/participants`),
    markAttendance: (b) => request('POST', '/api/admin/attendance', b),
    sendNotification: (b) => request('POST', '/api/admin/notifications', b),
    listUsers: () => request('GET', '/api/admin/users'),
    changeRole: (id, role) => request('PATCH', `/api/admin/users/${id}/role`, { role }),
    reports: () => request('GET', '/api/admin/reports'),
    stats: () => request('GET', '/api/admin/stats'),
    speakers: () => request('GET', '/api/admin/speakers'),
  };
})();

/* ===== Toast helper ===== */
function toast(message, type = '') {
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = message;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

/* ===== Format helpers ===== */
function fmtDate(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch { return iso; }
}
function fmtDateTime(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}
function initials(name) {
  if (!name) return '?';
  return name.split(' ').slice(0, 2).map(p => p[0]).join('').toUpperCase();
}

/* ===== Auth gate helper (call on protected pages) ===== */
async function requireStudent() {
  try {
    const me = await API.me();
    if (me.role !== 'Student') {
      window.location.href = '/login';
      return null;
    }
    return me;
  } catch {
    window.location.href = '/login';
    return null;
  }
}
async function requireAdmin() {
  try {
    const me = await API.me();
    if (me.role === 'Student') {
      window.location.href = '/login';
      return null;
    }
    return me;
  } catch {
    window.location.href = '/login';
    return null;
  }
}
