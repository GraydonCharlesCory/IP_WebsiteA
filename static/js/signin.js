/* Sign-in page: form sign-in, one-click role sign-in, Apple placeholder. */
(function () {
  const form = document.getElementById('signinForm');
  const buttons = form.querySelectorAll('button');

  function setBusy(busy) { buttons.forEach((b) => { b.disabled = busy; }); }

  async function run(action) {
    setBusy(true);
    try {
      const { user } = await action();
      location.href = Tutti.landingFor(user);
    } catch (error) {
      Tutti.reportError(error, 'sign-in');
      setBusy(false);
    }
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if (!email || !password) return Tutti.toast('Enter your email and password, or use one of the demo buttons.', 'error');
    run(() => api.signIn(email, password));
  });

  document.querySelectorAll('[data-role]').forEach((button) =>
    button.addEventListener('click', () => run(() => api.signInAs(button.dataset.role))));

  document.getElementById('appleButton').addEventListener('click', () =>
    Tutti.toast('Sign in with Apple is not available in the demo. Use the musician or director button instead.'));

  document.getElementById('eye').addEventListener('click', () => {
    const field = document.getElementById('password');
    field.type = field.type === 'password' ? 'text' : 'password';
  });

  api.sections().then(({ sections }) => {
    const total = (key) => sections.reduce((sum, s) => sum + s[key], 0);
    document.getElementById('stats').innerHTML =
      `<div><b>${total('musicians')}</b><span>musicians</span></div><div><b>${sections.length}</b><span>sections</span></div><div><b>${total('auditions')}</b><span>open auditions</span></div>`;
  }).catch((error) => Tutti.reportError(error, 'stats'));
})();
