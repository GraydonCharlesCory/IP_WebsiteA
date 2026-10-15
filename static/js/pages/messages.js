/* Messages: messages.html, ?c=<conversation id>, or ?to=<user id>[&opportunity=<id>][&submission=<id>]. */
(function () {
  const { esc, queryParam } = Tutti.util;
  const { conversationRow, threadHeader, bubble, emptyThread } = Tutti.messageViews;
  const root = document.getElementById('pageRoot');
  const POLL_MS = 5000;

  const state = {
    conversations: [],
    activeId: null,
    draft: null, // {user, context} while a first message to someone is being written
    messages: [], // server messages followed by local pending/failed ones
    signature: '',
    sending: false,
  };
  let nextLocalId = 1;

  const scaffold = () => `<div class="wrap page messages-page"><div class="inbox card">
    <aside class="inbox-list" id="convList" aria-label="Conversations"></aside>
    <section class="thread" id="thread"><div class="empty">Select a conversation.</div></section></div></div>`;

  const $ = (id) => document.getElementById(id);
  const failure = (error, context) => { console.error('Tutti messages', context, error); return error.message || 'Something went wrong. Please try again.'; };

  /* ---- List ---- */
  function renderList() {
    $('convList').innerHTML = state.conversations.length
      ? state.conversations.map((c) => conversationRow(c, state.activeId)).join('')
      : '<div class="empty small">No conversations yet. Message a director or musician from their profile or an opportunity.</div>';
  }

  async function refreshList() {
    const { conversations, unread_total: unread } = await api.conversations();
    state.conversations = conversations;
    Tutti.setUnreadBadge(unread);
    renderList();
  }

  /* ---- Thread ---- */
  function messagesMarkup() {
    return state.messages.length ? state.messages.map(bubble).join('') : emptyThread('No messages yet. Say hello below.');
  }

  function renderMessages(stickToBottom) {
    const box = $('messages');
    const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    box.innerHTML = messagesMarkup();
    if (stickToBottom || nearBottom) box.scrollTop = box.scrollHeight;
  }

  function renderThread(other, context) {
    $('thread').innerHTML = `${threadHeader(other, context)}
      <div class="messages" id="messages" aria-live="polite"></div>
      <div class="thread-error" id="threadError" role="alert" hidden></div>
      <form class="composer" id="composer">
        <textarea class="input" id="composerText" rows="1" maxlength="4000" placeholder="Write a message… (Enter to send, Shift+Enter for a new line)" aria-label="Message"></textarea>
        <button class="btn btn-primary" id="sendButton" type="submit">Send</button></form>`;
    renderMessages(true);
    $('composerText').focus();
  }

  function showThreadError(text) {
    const box = $('threadError');
    if (!box) return;
    box.textContent = text || '';
    box.hidden = !text;
  }

  async function markReadIfNeeded(conversationId) {
    const entry = state.conversations.find((c) => c.id === conversationId);
    if (!entry || !entry.unread_count) return;
    try {
      const { unread_total: unread } = await api.markConversationRead(conversationId);
      entry.unread_count = 0;
      Tutti.setUnreadBadge(unread);
      renderList();
    } catch (error) { failure(error, 'mark read'); }
  }

  async function openConversation(id) {
    state.activeId = id;
    state.draft = null;
    state.signature = '';
    renderList();
    try {
      const { conversation, messages } = await api.conversation(id);
      state.messages = messages;
      state.signature = signatureOf(messages);
      renderThread(conversation.other, conversation.context);
      history.replaceState(null, '', `messages.html?c=${id}`);
      await markReadIfNeeded(id);
    } catch (error) {
      $('thread').innerHTML = `<div class="empty"><h3>This conversation could not be opened</h3><p class="muted" style="margin-top:8px">${esc(failure(error, 'open conversation'))}</p></div>`;
    }
  }

  const signatureOf = (messages) => messages.map((m) => `${m.id}:${m.read}`).join(',');

  /* ---- Sending ---- */
  async function deliver(local) {
    state.sending = true;
    showThreadError('');
    try {
      if (state.draft) {
        const { user, context } = state.draft;
        const { conversation } = await api.startConversation({ user_id: user.id, body: local.body, audition_id: context.audition_id, submission_id: context.submission_id });
        state.draft = null;
        await refreshList();
        return openConversation(conversation.id);
      }
      const { message } = await api.sendMessage(state.activeId, local.body);
      Object.assign(local, message, { state: '' });
      renderMessages(true);
      refreshList().catch((error) => failure(error, 'refresh list'));
    } catch (error) {
      local.state = 'failed';
      showThreadError(failure(error, 'send message'));
      renderMessages(true);
    } finally {
      state.sending = false;
    }
  }

  function send(body) {
    const local = { localId: `local-${nextLocalId++}`, body, mine: true, created: new Date().toISOString(), state: 'sending' };
    state.messages.push(local);
    renderMessages(true);
    return deliver(local);
  }

  function retry(localId) {
    const local = state.messages.find((m) => m.localId === localId);
    if (!local || state.sending) return;
    local.state = 'sending';
    renderMessages(true);
    deliver(local);
  }

  function onComposerSubmit(event) {
    event.preventDefault();
    const field = $('composerText');
    const body = field.value.trim();
    if (!body || state.sending) return;
    field.value = '';
    send(body);
  }

  function onComposerKey(event) {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      $('composer').requestSubmit();
    }
  }

  /* ---- Polling: a reply from another account shows up without reloading ---- */
  async function poll() {
    if (document.hidden || state.sending) return;
    try {
      await refreshList();
      if (!state.activeId) return;
      const { messages } = await api.conversation(state.activeId);
      const signature = signatureOf(messages);
      if (signature === state.signature) return;
      state.signature = signature;
      const pending = state.messages.filter((m) => m.state);
      state.messages = messages.concat(pending);
      renderMessages(false);
      await markReadIfNeeded(state.activeId);
    } catch (error) { failure(error, 'poll'); }
  }

  /* ---- Deep links ---- */
  async function contextFromLink() {
    const context = { audition_id: Number(queryParam('opportunity')) || undefined, submission_id: Number(queryParam('submission')) || undefined };
    let opportunity = null;
    if (context.audition_id) {
      try { opportunity = (await api.opportunity(context.audition_id)).opportunity; } catch (error) { failure(error, 'link context'); }
    }
    return { context, chip: opportunity ? { opportunity: { id: opportunity.id, title: opportunity.title } } : (context.submission_id ? { submission_id: context.submission_id } : null) };
  }

  async function startDraftFor(userId) {
    const { musicians, directors } = await api.accounts();
    const other = musicians.concat(directors).find((u) => u.id === userId);
    if (!other) throw new Error('That person could not be found, so a message cannot be started.');
    const { context, chip } = await contextFromLink();
    state.activeId = null;
    state.draft = { user: other, context };
    state.messages = [];
    renderList();
    renderThread(other, chip);
  }

  async function openFromLink(me) {
    const conversationId = Number(queryParam('c'));
    const userId = Number(queryParam('to'));
    if (conversationId) return openConversation(conversationId);
    if (!userId) return state.conversations.length ? openConversation(state.conversations[0].id) : undefined;
    if (userId === me.id) throw new Error('You cannot message yourself.');
    const existing = state.conversations.find((c) => c.other.id === userId);
    return existing ? openConversation(existing.id) : startDraftFor(userId);
  }

  function wire() {
    $('convList').addEventListener('click', (event) => {
      const row = event.target.closest('[data-conversation-id]');
      if (row) openConversation(Number(row.dataset.conversationId));
    });
    $('thread').addEventListener('submit', (event) => { if (event.target.id === 'composer') onComposerSubmit(event); });
    $('thread').addEventListener('keydown', (event) => { if (event.target.id === 'composerText') onComposerKey(event); });
    $('thread').addEventListener('click', (event) => {
      const button = event.target.closest('[data-retry]');
      if (button) retry(button.dataset.retry);
    });
    setInterval(poll, POLL_MS);
  }

  Tutti.boot({ active: 'messages' }).then(async (me) => {
    root.innerHTML = scaffold();
    wire();
    try {
      await refreshList();
      await openFromLink(me);
    } catch (error) {
      $('thread').innerHTML = `<div class="empty"><h3>Messages could not be loaded</h3><p class="muted" style="margin-top:8px">${esc(failure(error, 'load'))}</p></div>`;
    }
  });
})();
