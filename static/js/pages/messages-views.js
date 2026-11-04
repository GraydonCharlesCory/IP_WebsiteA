/* Markup for the messages page: conversation list rows, thread header and bubbles. Tutti.messageViews */
(function () {
  const { esc, timeAgo } = Tutti.util;
  const avatar = (user) => Tutti.applicantAvatar(user);

  const roleLabel = (user) => (user.role === 'director' ? [user.ensemble, 'Director'].filter(Boolean).join(' · ') : (user.instrument || 'Musician'));

  function contextChip(context) {
    if (!context) return '';
    if (context.opportunity) return `<span class="tag brass ctx-chip" title="${esc(context.opportunity.title)}">${esc(context.opportunity.title)}</span>`;
    if (context.submission_id) return '<span class="tag grey ctx-chip">Application</span>';
    return '';
  }

  function conversationRow(conversation, activeId) {
    const last = conversation.last_message;
    const preview = last ? `${last.mine ? 'You: ' : ''}${last.body}` : 'No messages yet';
    const unread = conversation.unread_count > 0;
    return `<button class="conv ${conversation.id === activeId ? 'on' : ''} ${unread ? 'unread' : ''}" data-conversation-id="${conversation.id}">
      ${avatar(conversation.other)}
      <span class="conv-body">
        <span class="conv-top"><b>${esc(conversation.other.name)}</b><span class="conv-time">${last ? esc(timeAgo(last.created)) : ''}</span></span>
        <span class="conv-role">${esc(roleLabel(conversation.other))}</span>
        ${contextChip(conversation.context)}
        <span class="conv-preview">${esc(preview)}</span>
      </span>${unread ? `<span class="unread-dot" title="${conversation.unread_count} unread"></span>` : ''}</button>`;
  }

  function threadHeader(other, context) {
    const profile = other.handle && other.role === 'musician' ? `<a class="btn btn-ghost" href="profile.html?h=${encodeURIComponent(other.handle)}">View profile</a>` : '';
    return `<header class="thread-head">${avatar(other)}
      <div class="thread-who"><b>${esc(other.name)}</b><span class="small muted">${esc(roleLabel(other))}</span></div>
      ${contextChip(context)}<div class="spacer"></div>${profile}</header>`;
  }

  /* message: {id, body, created, mine} plus optional local state 'sending' | 'failed' */
  function bubble(message) {
    const state = message.state === 'sending' ? '<span class="state">Sending…</span>'
      : message.state === 'failed' ? '<button class="state failed" data-retry="' + esc(message.localId) + '">Not sent. Tap to retry</button>'
        : `<span class="state">${esc(timeAgo(message.created))}</span>`;
    return `<div class="bubble-row ${message.mine ? 'mine' : 'theirs'}"><div class="bubble ${message.state || ''}">${esc(message.body)}</div>${state}</div>`;
  }

  const emptyThread = (text) => `<div class="empty">${esc(text)}</div>`;

  return void (Tutti.messageViews = { conversationRow, threadHeader, bubble, emptyThread, contextChip });
})();
