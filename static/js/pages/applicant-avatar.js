/* Avatar for an applicant: a neutral "?" circle while anonymous (blind review), else the normal avatar. Tutti.applicantAvatar(user, size) */
(function () {
  const { esc } = Tutti.util;

  Tutti.applicantAvatar = (user, size = '') => (user.anonymous
    ? `<div class="av ${size} g0" title="${esc(user.label || user.name)}" aria-label="Anonymous applicant">?</div>`
    : Tutti.components.avatar(user, size));
})();
