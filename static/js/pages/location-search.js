/* Explicit US geography only; curated city shortcuts, never geocoding or data repair. */
(function () {
  const { esc } = Tutti.util;
  // Census regions: https://www.bls.gov/lau/laurdqa.htm
  const regions = {
    Northeast: 'CT:Connecticut|ME:Maine|MA:Massachusetts|NH:New Hampshire|RI:Rhode Island|VT:Vermont|NJ:New Jersey|NY:New York|PA:Pennsylvania',
    Midwest: 'IL:Illinois|IN:Indiana|MI:Michigan|OH:Ohio|WI:Wisconsin|IA:Iowa|KS:Kansas|MN:Minnesota|MO:Missouri|NE:Nebraska|ND:North Dakota|SD:South Dakota',
    South: 'DE:Delaware|DC:District of Columbia|FL:Florida|GA:Georgia|MD:Maryland|NC:North Carolina|SC:South Carolina|VA:Virginia|WV:West Virginia|AL:Alabama|KY:Kentucky|MS:Mississippi|TN:Tennessee|AR:Arkansas|LA:Louisiana|OK:Oklahoma|TX:Texas',
    West: 'AZ:Arizona|CO:Colorado|ID:Idaho|MT:Montana|NV:Nevada|NM:New Mexico|UT:Utah|WY:Wyoming|AK:Alaska|CA:California|HI:Hawaii|OR:Oregon|WA:Washington'
  };
  const normalize = value => String(value || '').trim().replace(/\s+/g, ' ').toLowerCase();
  const states = {};
  Object.entries(regions).forEach(([region, values]) => values.split('|').forEach(value => {
    const [code, name] = value.split(':');
    states[code] = { name, region };
  }));
  const stateCode = value => normalize(value) === 'd.c.' ? 'DC' : Object.keys(states).find(code => normalize(code) === normalize(value) || normalize(states[code].name) === normalize(value)) || '';
  const usCountry = value => ['us','usa','u.s.','u.s.a.','united states','united states of america'].includes(normalize(value));
  // Editorial shortcuts, not a population ranking or an exhaustive city list.
  const cities = {
    CT: ['Hartford','New Haven'], ME: ['Portland'], MA: ['Boston'], NH: ['Manchester'], RI: ['Providence'], VT: ['Burlington'], NJ: ['Newark'], NY: ['New York','Buffalo'], PA: ['Philadelphia','Pittsburgh'],
    IL: ['Chicago'], IN: ['Indianapolis'], MI: ['Detroit'], OH: ['Columbus','Cleveland','Cincinnati'], WI: ['Milwaukee','Madison'], IA: ['Des Moines'], KS: ['Wichita'], MN: ['Minneapolis','Saint Paul'], MO: ['Kansas City','Saint Louis'], NE: ['Omaha'], ND: ['Fargo'], SD: ['Sioux Falls'],
    DE: ['Wilmington'], DC: ['Washington'], FL: ['Miami','Orlando','Tampa','Jacksonville'], GA: ['Atlanta'], MD: ['Baltimore'], NC: ['Charlotte','Raleigh'], SC: ['Charleston'], VA: ['Richmond'], WV: ['Charleston'], AL: ['Birmingham'], KY: ['Louisville'], MS: ['Jackson'], TN: ['Nashville','Memphis'], AR: ['Little Rock'], LA: ['New Orleans'], OK: ['Oklahoma City','Tulsa'], TX: ['Austin','Dallas','Houston','San Antonio'],
    AZ: ['Phoenix','Tucson'], CO: ['Denver'], ID: ['Boise'], MT: ['Billings'], NV: ['Las Vegas','Reno'], NM: ['Albuquerque'], UT: ['Salt Lake City'], WY: ['Cheyenne'], AK: ['Anchorage'], CA: ['Los Angeles','San Francisco','San Diego','San Jose','Sacramento','Oakland'], HI: ['Honolulu'], OR: ['Portland'], WA: ['Seattle','Spokane']
  };
  const catalog = Object.entries(cities).flatMap(([state, names]) => names.map(city => ({ city, state, region: states[state].region, key: `${city}|${state}` }))).sort((a,b) => a.key.localeCompare(b.key));
  const cityName = value => normalize(value).replace(/^st\.?\s+/, 'saint ');
  function parse(record) {
    if (record.country && !usCountry(record.country)) return null;
    const location = String(record.location || '').trim();
    const parts = location.split(',').map(v => v.trim());
    if (parts.length > 3 || (parts.length === 3 && !usCountry(parts[2]))) return null;
    let city = '', state = '';
    if (parts.length >= 2) {
      city = parts[0]; state = stateCode(parts[1]);
      if (!state || !city) return null;
      // Georgia is also a country: a free-form full-name suffix alone is ambiguous.
      if (normalize(parts[1]) === 'georgia' && !record.country && parts.length !== 3 && !record.state) return null;
      if (record.city && cityName(record.city) !== cityName(city)) return null;
    }
    // Structured city/state is authoritative only when the other explicit fields agree.
    if (record.state) {
      const explicit = stateCode(record.state);
      if (!explicit || (state && explicit !== state)) return null;
      state = explicit;
      if (record.city && city && cityName(record.city) !== cityName(city)) return null;
      city = String(record.city || city || location).trim();
    }
    if (!state) return null; // A bare city (even New York) never implies a country/state.
    return { city, state, region: states[state].region };
  }
  function matches(record, filters) {
    const text = [record.location, record.city, record.state].filter(Boolean).join(' ').toLowerCase();
    if (filters.location && !text.includes(normalize(filters.location))) return false;
    if (!filters.region && !filters.city) return true;
    const place = parse(record);
    if (!place || (filters.region && filters.region !== place.region)) return false;
    if (!filters.city) return true;
    const selected = catalog.find(item => item.key === filters.city);
    return !!selected && selected.state === place.state && cityName(selected.city) === cityName(place.city);
  }
  const cityOptions = region => `<option value="">All cities</option>${catalog.filter(item => !region || item.region === region).map(item => `<option value="${esc(item.key)}">${esc(item.city)}, ${item.state}</option>`).join('')}`;
  function markup(prefix) {
    return `<div class="location-filters"><label class="field" for="${prefix}Region">U.S. region<select class="input" id="${prefix}Region" data-geo="region" aria-describedby="${prefix}GeoHelp"><option value="">All regions</option>${Object.keys(regions).map(region => `<option>${region}</option>`).join('')}</select></label><label class="field" for="${prefix}City">Major city<select class="input" id="${prefix}City" data-geo="city" aria-describedby="${prefix}GeoHelp">${cityOptions('')}</select></label><label class="field" for="${prefix}Location">Location text<input class="input" type="search" id="${prefix}Location" data-geo="location" placeholder="Any city, state or country" aria-describedby="${prefix}GeoHelp"></label><p class="small muted" id="${prefix}GeoHelp">Curated city shortcuts, not all cities. Region changes clear incompatible cities. All regions shows every city. Location text narrows these choices; use All regions and All cities for smaller, international or unspecified places.</p></div>`;
  }
  function bind(form, filters, render) {
    const controls = Object.fromEntries([...form.querySelectorAll('[data-geo]')].map(input => [input.dataset.geo, input]));
    const sync = () => {
      if (filters.city && !catalog.some(item => item.key === filters.city && (!filters.region || item.region === filters.region))) filters.city = '';
      controls.region.value = filters.region || '';
      controls.city.innerHTML = cityOptions(filters.region);
      controls.city.value = filters.city || '';
      controls.location.value = filters.location || '';
    };
    Object.entries(controls).forEach(([key, input]) => input.addEventListener('input', () => {
      filters[key] = input.value;
      if (key === 'region') sync();
      render();
    }));
    sync();
    return { sync };
  }
  Tutti.locationSearch = { regions, states, catalog, parse, matches, markup, bind };
})();
