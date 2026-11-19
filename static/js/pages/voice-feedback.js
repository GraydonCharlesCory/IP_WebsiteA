/* Speech recognition is opt-in and browser/provider dependent; typing always works. */
(function () {
  function mount(textarea) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const help = document.createElement('p');
    help.className = 'small muted';
    textarea.after(help);
    if (!Recognition) {
      help.textContent = 'Voice-to-text is unavailable in this browser. Type your feedback above.';
      return;
    }
    help.textContent = 'Optional voice-to-text uses your browser’s speech service, which may process speech online. Review the transcript before sharing. Typing is always available.';
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'btn btn-ghost'; button.textContent = 'Dictate feedback';
    help.after(button);
    let recognition = null;
    button.onclick = () => {
      if (recognition) { recognition.stop(); return; }
      recognition = new Recognition();
      recognition.onresult = (event) => {
        textarea.value += (textarea.value ? ' ' : '') + event.results[0][0].transcript;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      };
      recognition.onerror = (event) => Tutti.reportError(new Error(`Voice input failed (${event.error}). Check microphone permission or type instead.`), 'voice feedback');
      recognition.onend = () => { recognition = null; button.textContent = 'Dictate feedback'; };
      try { recognition.start(); button.textContent = 'Stop dictation'; }
      catch (error) { recognition = null; Tutti.reportError(error, 'start voice input; type instead'); }
    };
  }
  Tutti.voiceFeedback = { mount };
})();
