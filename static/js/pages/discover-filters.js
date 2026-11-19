/* Filter state of the opportunity board and its URL query string: Tutti.discoverFilters */
(function () {
  const { esc } = Tutti.util;

  const FILTER_KEYS = ['q', 'category', 'type', 'instrument', 'genre', 'location', 'level', 'paid', 'video_round', 'deadline_before', 'sort'];
  const DEFAULT_SORT = 'deadline';

  const CATEGORY_OPTIONS = [['', 'All sections'], ['students', 'Students'], ['orchestral', 'Orchestral'], ['jazz', 'Jazz']];
  const TYPE_OPTIONS = [['', 'All opportunities'], ['audition', 'Auditions'], ['gig', 'Gigs'], ['grant', 'Grants'], ['residency', 'Residencies'], ['college_audition', 'High-school: College auditions'], ['summer_camp', 'High-school: Summer camps']];
  const LEVEL_OPTIONS = [['', 'Any level'], ['student', 'Student'], ['college', 'College'], ['semi-pro', 'Semi-pro'], ['pro', 'Pro']];
  const PAID_OPTIONS = [['', 'Paid or unpaid'], ['1', 'Paid'], ['0', 'Unpaid']];
  const VIDEO_OPTIONS = [['', 'Any entry'], ['1', 'Video round accepted']];
  const SORT_OPTIONS = [['deadline', 'Soonest deadline'], ['newest', 'Newest']];

  function fromQueryString(search) {
    const params = new URLSearchParams(search);
    const filters = {};
    FILTER_KEYS.forEach((key) => { filters[key] = params.get(key) || ''; });
    return filters;
  }

  /* Query string with only the non-default filters, so shared links stay short. */
  function toQueryString(filters) {
    const params = new URLSearchParams();
    FILTER_KEYS.forEach((key) => {
      if (filters[key] && !(key === 'sort' && filters[key] === DEFAULT_SORT)) params.set(key, filters[key]);
    });
    const text = params.toString();
    return text ? `?${text}` : '';
  }

  const activeCount = (filters) => FILTER_KEYS.filter((key) => key !== 'sort' && filters[key]).length;

  function select(id, label, options, value) {
    const list = options.map(([optionValue, text]) => `<option value="${esc(optionValue)}" ${optionValue === value ? 'selected' : ''}>${esc(text)}</option>`).join('');
    return `<label class="filter-field"><span>${esc(label)}</span><select class="input" data-filter="${id}">${list}</select></label>`;
  }

  /* Options for the instrument and location selects, from every opportunity on the board. */
  function optionsFrom(opportunities) {
    const sorted = (values) => [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
    const instruments = sorted(opportunities.flatMap((opp) => opp.instruments || []));
    const cities = sorted(opportunities.map((opp) => opp.city));
    return {
      instrument: [['', 'Any instrument'], ...instruments.map((name) => [name, name])],
      location: [['', 'Anywhere'], ...cities.map((name) => [name, name])],
    };
  }

  function controlsMarkup(filters, choices) {
    return `<div class="filter-grid">
      ${select('type', 'Type', TYPE_OPTIONS, filters.type)}
      ${select('instrument', 'Instrument', choices.instrument, filters.instrument)}
      <label class="filter-field"><span>Genre keywords</span><input class="input" data-filter="genre" value="${esc(filters.genre || '')}" placeholder="e.g. jazz" aria-describedby="genreHelp"></label>
      ${select('location', 'Location', choices.location, filters.location)}
      ${select('level', 'Level', LEVEL_OPTIONS, filters.level)}
      ${select('paid', 'Pay', PAID_OPTIONS, filters.paid)}
      ${select('video_round', 'Entry', VIDEO_OPTIONS, filters.video_round)}
      <label class="filter-field"><span>Closes by</span><input class="input" type="date" data-filter="deadline_before" value="${esc(filters.deadline_before)}"></label>
      ${select('sort', 'Sort', SORT_OPTIONS, filters.sort || DEFAULT_SORT)}</div><p class="small muted" id="genreHelp">Genre keywords search title, ensemble and description; sections are not genre labels.</p>`;
  }

  Tutti.discoverFilters = { FILTER_KEYS, fromQueryString, toQueryString, activeCount, optionsFrom, controlsMarkup, TYPE_OPTIONS, CATEGORY_OPTIONS };
})();
