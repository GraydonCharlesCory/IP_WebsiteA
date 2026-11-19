/* Small pure helpers shared by every page: window.Tutti.util */
(function () {
  const Tutti = (window.Tutti = window.Tutti || {});
  const SECTIONS = [
    { key: 'students', label: 'Students', css: 'students' },
    { key: 'orchestral', label: 'Orchestral', css: 'orch' },
    { key: 'jazz', label: 'Jazz', css: 'jazz' },
  ];

  const esc = (value) =>
    String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function section(key) {
    return SECTIONS.find((s) => s.key === key) || { key, label: key, css: 'grey' };
  }

  /* 134 -> "2:14" */
  function duration(seconds) {
    const total = Math.max(0, Math.round(seconds || 0));
    return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
  }

  /* Accepts "2:14" or "134" and returns seconds, or null when it is not a time. */
  function parseTime(text) {
    const match = /^(\d+):([0-5]?\d)$/.exec(String(text).trim());
    if (match) return Number(match[1]) * 60 + Number(match[2]);
    return /^\d+$/.test(String(text).trim()) ? Number(text) : null;
  }

  function date(iso, options = { month: 'short', day: 'numeric' }) {
    const parsed = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
    return parsed.toLocaleDateString('en-US', options);
  }

  function timeAgo(iso) {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes} min ago`;
    if (minutes < 1440) return `${Math.round(minutes / 60)} h ago`;
    const days = Math.round(minutes / 1440);
    return days < 8 ? `${days} d ago` : date(iso);
  }

  function daysUntil(isoDate) {
    return Math.ceil((new Date(`${isoDate}T23:59:59`).getTime() - Date.now()) / 86400000);
  }

  const queryParam = (name) => new URLSearchParams(location.search).get(name);

  Tutti.util = { SECTIONS, esc, section, duration, parseTime, date, timeAgo, daysUntil, queryParam };
})();
