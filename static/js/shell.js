/* Shared page shell: top bar, account switcher, toasts, page boot.
   Requires (in this order): api.js, util.js, components.js, shell.js.

   Page recipe:
     <div data-shell-header></div> ...page markup...
     Tutti.boot({ active: 'home', requireRole: 'musician' }).then((user) => { ...render... });
   `active` is one of: home, students, orchestral, jazz, auditions (musician), dashboard (director),
   discover, applications, teachers, messages. Tutti.setUnreadBadge(n) updates the Messages badge. */
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
  const landingFor = (user) => (user.role === 'director' ? 'director.html' : 'home.html');

  function navLinks(user) {
    const links = [{ href: 'home.html', label: 'Home', key: 'home' }];
    SECTIONS.forEach((s) => links.push({ href: `section.html?s=${s.key}`, label: s.label, key: s.key, dot: s.key }));
    if (user && user.role === 'musician') links.push({ href: `section.html?s=${user.category}#auditions`, label: 'Auditions', key: 'auditions' });
    if (user && user.role === 'director') links.push({ href: 'director.html', label: 'My auditions', key: 'dashboard' });
    if (user) links.push({ href: 'discover.html', label: 'Discover', key: 'discover' });
    if (user && user.role === 'musician') links.push({ href: 'applications.html', label: 'Applications', key: 'applications' });
    links.push({ href: 'teachers.html', label: 'Teachers', key: 'teachers' });
    return links;
  }

  const myPageHref = (user) => (user.role === 'musician' ? `profile.html?h=${encodeURIComponent(user.handle)}` : 'director.html');

  const ICON_MESSAGES = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>';

  /* Show (or hide, when zero) the unread count on the top-bar Messages icon. */
  function setUnreadBadge(count) {
    const badge = document.getElementById('messagesBadge');
    if (!badge) return;
    badge.textContent = count > 99 ? '99+' : String(count);
    badge.hidden = !(count > 0);
  }

  function messagesMarkup(active) {
    return `<a class="messages-link ${active === 'messages' ? 'on' : ''}" href="messages.html" title="Messages" aria-label="Messages">${ICON_MESSAGES}<span class="badge-count" id="messagesBadge" hidden>0</span></a>`;
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
    host.innerHTML = `<div class="wrap">
      <a class="logo" href="${user ? landingFor(user) : 'index.html'}"><span class="logo-mark">${LOGO}</span>Tutti</a>
      <nav class="nav">${navLinks(user).map((l) =>
        `<a href="${l.href}" class="${l.key === active ? 'on' : ''}">${l.dot ? dot(l.dot) : ''}${esc(l.label)}</a>`).join('')}</nav>
      <div class="spacer"></div>${user ? messagesMarkup(active) : ''}${meMarkup(user)}</div>`;
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
      setUnreadBadge(user.unread_messages || 0);
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
  Tutti.setUnreadBadge = setUnreadBadge;
})();
