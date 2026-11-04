/* Gig page side cards: musicians mark availability, the posting director reads the sub list. Tutti.gigAvailability */
(function () {
  const { esc, timeAgo } = Tutti.util;
  const { avatar } = Tutti.components;
  const { AVAILABILITY_LABELS, messageHref, profileHref } = Tutti.opportunityCards;
  const { privateNote } = Tutti.pageUtil;

  function musicianCard(gig) {
    if (gig.status !== 'open') return '<div class="card pad stack"><div class="eyebrow">Closed</div><p class="t2">This gig is no longer taking availability.</p></div>';
    const buttons = Object.entries(AVAILABILITY_LABELS).map(([status, label]) =>
      `<button type="button" class="avail ${status} ${gig.my_availability === status ? 'on' : ''}" data-status="${status}" aria-pressed="${gig.my_availability === status}">${label}</button>`).join('');
    const current = gig.my_availability ? `You are marked <b>${AVAILABILITY_LABELS[gig.my_availability]}</b>.` : 'Let the director know if you can play this one.';
    return `<div class="card pad stack" id="availabilityCard"><div class="eyebrow">Your availability</div>
      <div class="avail-row">${buttons}</div><p class="small t2">${current}</p>
      ${privateNote('Only the posting director sees who marked available.')}</div>`;
  }

  function subRow(person) {
    return `<div class="sub-row">${avatar(person, 'sm')}<a class="who" href="${profileHref(person)}"><b>${esc(person.name)}</b>
      <span>${esc(person.instrument)}${person.location ? ` · ${esc(person.location)}` : ''} · marked ${timeAgo(person.marked)}</span></a>
      <a class="btn btn-ghost sub-msg" href="${messageHref(person.id)}">Message</a></div>`;
  }

  function subGroup(label, people) {
    if (!people.length) return '';
    return `<div class="sub-group"><div class="eyebrow">${label} · ${people.length}</div>${people.map(subRow).join('')}</div>`;
  }

  function ownerCard(list) {
    const body = subGroup('Available', list.available) + subGroup('Maybe', list.maybe);
    return `<div class="card pad stack"><div class="eyebrow">Sub list</div>
      ${body || '<p class="small muted">Nobody has marked available yet.</p>'}
      ${privateNote('Only you can see this list.')}</div>`;
  }

  function viewerCard() {
    return '<div class="card pad stack"><div class="eyebrow">Director view</div><p class="t2">Only musicians mark availability, and only the posting director sees the sub list.</p></div>';
  }

  /* Resolves to the HTML for the side column's main card. */
  async function mainCard(gig, user) {
    if (user.role === 'musician') return musicianCard(gig);
    return gig.owned_by_me ? ownerCard(await api.subList(gig.id)) : viewerCard();
  }

  /* Wire the availability buttons; `onChange(status)` runs after the server saved the choice. */
  function wireMusicianCard(gig, onChange) {
    const card = document.getElementById('availabilityCard');
    if (!card) return;
    card.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-status]');
      if (!button || button.disabled) return;
      card.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      try {
        const { availability } = await api.markAvailability(gig.id, button.dataset.status);
        gig.my_availability = availability.status;
        Tutti.toast(`Marked ${AVAILABILITY_LABELS[availability.status].toLowerCase()}.`, 'ok');
        onChange();
      } catch (error) {
        Tutti.reportError(error, 'mark availability');
        card.querySelectorAll('button').forEach((b) => { b.disabled = false; });
      }
    });
  }

  Tutti.gigAvailability = { mainCard, wireMusicianCard, musicianCard };
})();
