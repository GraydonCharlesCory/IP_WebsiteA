/* Shared page shell: top bar, account switcher, toasts, page boot.
   Requires (in this order): api.js, util.js, components.js, shell.js.

   Page recipe:
     <div data-shell-header></div> ...page markup...
     Tutti.boot({ active: 'home', requireRole: 'musician' }).then((user) => { ...render... });
   `active` identifies Discovery, applications, dashboard, manage, schools, feed or teachers. */
(function () {
  const { esc, SECTIONS } = Tutti.util;
  const { avatar, dot } = Tutti.components;
  const LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="#1A1405" stroke-width="2.4" stroke-linecap="round"><path d="M4 10v4M8 6v12M12 3v18M16 7v10M20 10v4"/></svg>';
  const CARET = '<svg class="caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg>';

  /* ---- Toasts ---- */
  function toast(message, kind = '') {
    let host = document.querySelector('.toasts');
    if (!host) {
      host = document.createElement('div');
      host.className = 'toasts';
      host.setAttribute('role', 'status');
      document.body.appendChild(host);
    }
    const item = document.createElement('div');
    item.className = `toast ${kind}`;
    item.textContent = message;
    host.appendChild(item);
    setTimeout(() => item.remove(), kind === 'error' ? 7000 : 4000);
  }

  /* Report a failure to the person and to the console. */
  function reportError(error, context = '') {
    console.error('Tutti error', context, error);
    toast(error.message || 'Something went wrong. Please try again.', 'error');
  }

  /* ---- Navigation ---- */
  const landingFor = () => 'discover.html';

  function navLinks(user) {
    const links = [{ href: 'discover.html', label: 'Discover', key: 'discover' }, {href:'students.html',label:'For Students',key:'students'}];
    if (user && user.role === 'director') links.push({ href: 'director.html', label: 'My auditions', key: 'dashboard' });
    if (user && user.role === 'musician') links.push({ href: 'applications.html', label: 'Auditions & applications', key: 'applications' });
    if (user && ['director','school'].includes(user.role)) links.push({ href: 'manage.html', label: 'Manage opportunities', key: 'manage' });
    links.push({ href: 'schools.html', label: 'Schools', key: 'schools' });
    links.push({ href: 'feed.html', label: 'Community', key: 'home' });
    links.push({ href: 'teachers.html', label: 'Teachers', key: 'teachers' });
    return links;
  }

  const myPageHref = (user) => (user.role === 'musician' ? `profile.html?h=${encodeURIComponent(user.handle)}` : user.role === 'school' ? 'schools.html' : 'director.html');

  function messagesMarkup(active) {
    return '<a class="btn btn-ghost" href="notices.html">Notices</a>';
  }

  function meMarkup(user) {
    if (!user) return '<a class="btn btn-primary signin-link" href="index.html">Sign in</a>';
    return `<div class="me-wrap">
      <button class="me-button" id="meButton" aria-haspopup="true" aria-expanded="false" title="Switch demo account">
        ${avatar(user, 'sm')}<span class="role-pill">${esc(user.role)}</span>${CARET}</button>
      <div class="switcher" id="switcher" role="menu"></div></div>`;
  }

  function renderHeader(user, active) {
    const host = document.querySelector('[data-shell-header]') || document.body.insertAdjacentElement('afterbegin', document.createElement('div'));
    host.className = 'topbar';
    document.body.classList.add('shell-ready');
    host.innerHTML = `<a class="skip-link" href="#${document.getElementById('pageRoot') ? 'pageRoot' : 'content'}">Skip to content</a><aside class="sidebar">
      <a class="logo" href="${user ? landingFor(user) : 'index.html'}"><span class="logo-mark">${LOGO}</span>Tutti</a>
      <nav class="nav">${navLinks(user).map((l) =>
        `<a href="${l.href}" class="${l.key === active ? 'on' : ''}">${l.dot ? dot(l.dot) : ''}${esc(l.label)}</a>`).join('')}</nav>
      <div class="side-identity">${user ? `${avatar(user, 'sm')}<div>${esc(user.name)}<br><span class="muted small">${esc(user.role)}</span></div>` : 'A place for your next movement.'}</div></aside>
      <header class="utility"><span>Tutti / ${esc(navLinks(user).find(l => l.key === active)?.label || 'Your workspace')}</span><div class="utility-actions"><button class="btn btn-ghost" id="themeButton" aria-label="Toggle light or dark appearance" type="button">Dark appearance</button>${user && user.role === 'musician' ? messagesMarkup(active) : ''}${meMarkup(user)}</div></header>`;
    const themeButton = document.getElementById('themeButton');
    const syncTheme = dark => {
      document.body.classList.toggle('dark', dark);
      themeButton.textContent = dark ? 'Light appearance' : 'Dark appearance';
      themeButton.setAttribute('aria-pressed', String(dark));
    };
    try { syncTheme(localStorage.getItem('tutti-appearance') === 'dark'); }
    catch (error) { console.error('Tutti appearance could not be restored; use the appearance button to change it.', error); }
    themeButton.onclick = () => {
      syncTheme(!document.body.classList.contains('dark'));
      try { localStorage.setItem('tutti-appearance', document.body.classList.contains('dark') ? 'dark' : 'light'); }
      catch (error) { reportError(new Error('Appearance changed for this page only. Browser storage is unavailable.'), 'save appearance'); }
    };
  }

  /* ---- Account switcher ---- */
  function accountButton(account, current) {
    const sub = account.role === 'director' ? account.ensemble : account.instrument;
    const isCurrent = current && current.id === account.id;
    return `<button class="acct ${isCurrent ? 'current' : ''}" data-user-id="${account.id}" role="menuitem">
      ${avatar(account, 'sm')}<span class="who"><b>${esc(account.name)}</b><span>${esc(sub)}</span></span>${isCurrent ? '<span class="check">✓</span>' : ''}</button>`;
  }

  async function wireSwitcher(user) {
    const button = document.getElementById('meButton');
    const menu = document.getElementById('switcher');
    if (!button) return;
    let loaded = false;
    const close = () => { menu.classList.remove('open'); button.setAttribute('aria-expanded', 'false'); };
    button.addEventListener('click', async (event) => {
      event.stopPropagation();
      const opening = !menu.classList.contains('open');
      if (!opening) return close();
      if (!loaded) {
        try {
          const accounts = await api.accounts();
          menu.innerHTML = `<h4>Musicians</h4>${accounts.musicians.map((a) => accountButton(a, user)).join('')}
            <h4>Directors</h4>${accounts.directors.map((a) => accountButton(a, user)).join('')}
            <h4>Schools</h4>${(accounts.schools || []).map((a) => accountButton(a, user)).join('')}
            <div class="foot"><a class="acct" href="${myPageHref(user)}"><span class="who"><b>${user.role === 'musician' ? 'View my profile' : 'My auditions'}</b></span></a><button class="acct" id="signOutButton"><span class="who"><b>Sign out</b></span></button></div>`;
          loaded = true;
        } catch (error) { return reportError(error, 'account list'); }
      }
      menu.classList.add('open');
      button.setAttribute('aria-expanded', 'true');
    });
    document.addEventListener('click', (event) => { if (!menu.contains(event.target)) close(); });
    menu.addEventListener('click', async (event) => {
      const target = event.target.closest('button');
      if (!target) return;
      try {
        if (target.id === 'signOutButton') {
          await api.signOut();
          location.href = 'index.html';
        } else if (target.dataset.userId) {
          const { user: next } = await api.switchTo(Number(target.dataset.userId));
          if (next.role === user.role) location.reload();
          else location.href = landingFor(next);
        }
      } catch (error) { reportError(error, 'account switch'); }
    });
  }

  /* ---- Boot ---- */
  /* options: active, requireAuth (default true), requireRole ('musician' | 'director').
     Resolves to the signed-in user (or null on public pages with requireAuth: false). */
  async function boot(options = {}) {
    const requireAuth = options.requireAuth !== false;
    let user = null;
    try {
      user = (await api.me()).user;
    } catch (error) {
      renderHeader(null, options.active);
      reportError(error, 'boot');
      throw error;
    }
    if (!user && (requireAuth || options.requireRole)) {
      location.replace('index.html');
      return new Promise(() => {});
    }
    if (user && options.requireRole && user.role !== options.requireRole) {
      sessionStorage.setItem('tutti-flash', `That page is for ${options.requireRole}s. You are signed in as a ${user.role}.`);
      location.replace(landingFor(user));
      return new Promise(() => {});
    }
    renderHeader(user, options.active);
    if (user) {
      wireSwitcher(user);
    }
    const flash = sessionStorage.getItem('tutti-flash');
    if (flash) { sessionStorage.removeItem('tutti-flash'); toast(flash); }
    Tutti.components.wire();
    return user;
  }

  Tutti.toast = toast;
  Tutti.reportError = reportError;
  Tutti.landingFor = landingFor;
  Tutti.boot = boot;
})();
