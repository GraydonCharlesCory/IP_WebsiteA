const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {Tutti:{util:{esc:String}}};
vm.runInNewContext(fs.readFileSync('static/js/pages/location-search.js','utf8'), context);
vm.runInNewContext(fs.readFileSync('static/js/pages/discovery-shared.js','utf8'), context);
const geo = context.Tutti.locationSearch;
const match = (record, filters) => geo.matches(record,filters);
const chicago = {city:'Chicago',state:'IL',location:'Chicago, IL',title:'Chamber music',instruments:['Viola'],genre:'Classical',type:'audition',eligibility:['college']};
// Independent expected grouping covers every state and DC, not just catalog cities.
const expected = {
  Northeast:'CT ME MA NH RI VT NJ NY PA',
  Midwest:'IL IN MI OH WI IA KS MN MO NE ND SD',
  South:'DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX',
  West:'AZ CO ID MT NV NM UT WY AK CA HI OR WA'
};
assert.equal(Object.keys(geo.states).length,51);
for (const [region, codes] of Object.entries(expected)) {
  for (const state of codes.split(' ')) {
    assert.equal(geo.states[state].region,region);
    assert(match({city:'Unlisted smaller town',state},{region}));
    assert(match({location:`Unlisted smaller town, ${state}`},{region}));
    assert(match({location:`Unlisted smaller town, ${geo.states[state].name}, USA`},{region}));
    assert(geo.catalog.some(item=>item.state===state));
  }
}
assert.equal(new Set(geo.catalog.map(item=>item.key)).size,geo.catalog.length);
for (const item of geo.catalog) {
  assert(match({location:`${item.city}, ${item.state}`},{region:item.region,city:item.key}));
  assert(!match({location:`${item.city} Heights, ${item.state}`},{city:item.key}));
}
for (const location of ['Chicago','New York','Portland','Springfield','London, England','Toronto, ON','Chicago, Illinois, Canada','Chicago, IL, USA, Europe','California dreaming','CA','Chicagoland, ILL']) {
  assert.equal(geo.parse({location}),null,location);
  assert(match({location},{location}),'All-region fallback retains unknown locations');
  assert(!match({location},{region:'Midwest'}));
}
for (const record of [chicago,{city:'Chicago',state:'Illinois'},{location:' Chicago , illinois '},{location:'Chicago, IL, United States'},{city:'Chicago',location:'Chicago, IL'}]) {
  assert(match(record,{region:'Midwest',city:'Chicago|IL'}));
  assert(!match(record,{region:'West'}));
  assert(!match(record,{city:'Chicago Heights|IL'}));
}
for (const record of [{city:'Chicago',state:'CA',location:'Chicago, IL'},{city:'Boston',state:'IL',location:'Chicago, IL'},{location:'Chicago, IL',country:'Canada'},{location:'Chicago, IL',state:'invalid'}]) {
  assert.equal(geo.parse(record),null);
}
assert(match({location:'St. Louis, MO'},{city:'Saint Louis|MO'}));
assert(match({location:'St Paul, MN'},{city:'Saint Paul|MN'}));
assert(match({location:'Washington, D.C.'},{city:'Washington|DC'}));
assert.equal(geo.parse({location:'Tbilisi, Georgia'}),null);
assert.equal(geo.parse({location:'Atlanta, Georgia'}),null);
assert(match({location:'Atlanta, Georgia, US'},{region:'South'}));
assert(!match({location:'Portland, ME'},{city:'Portland|OR'}));
assert(!match({location:'Charleston, SC'},{city:'Charleston|WV'}));
assert(match(chicago,{region:'Midwest',city:'Chicago|IL',location:'chicago'}));
assert(!match(chicago,{region:'Midwest',city:'Chicago|IL',location:'Boston'}));
assert(!match(chicago,{region:'South',city:'Chicago|IL'}));
const filters={q:'Chamber',instrument:'viola',genre:'Classical',type:'audition',level:'college',region:'Midwest',city:'Chicago|IL',location:'IL'};
assert(context.Tutti.discovery.matches(chicago,filters));
for (const [key,value] of Object.entries({q:'not found',instrument:'trumpet',genre:'Jazz',type:'grant',level:'high_school',region:'West',city:'Boston|MA',location:'Boston'})) {
  assert(!context.Tutti.discovery.matches(chicago,{...filters,[key]:value}),`${key} must AND`);
}
// Minimal DOM stand-in verifies state transitions independently of rendered workflows.
const controls=Object.fromEntries(['region','city','location'].map(key=>[key,{dataset:{geo:key},value:'',addEventListener(event,handler){this.handler=handler;}}]));
const form={querySelectorAll:()=>Object.values(controls)};
const state={region:'Midwest',city:'Chicago|IL',location:'IL'};
let rendered=0;
const binding=geo.bind(form,state,()=>rendered++);
controls.region.value='West';controls.region.handler();
assert.equal(state.city,'');assert.equal(controls.city.value,'');assert.equal(state.location,'IL');assert.equal(rendered,1);
state.region='';state.city='Chicago|IL';binding.sync();
assert.equal(controls.city.value,'Chicago|IL');assert(controls.city.innerHTML.includes('Boston|MA'));
Object.keys(state).forEach(key=>{state[key]='';});binding.sync();
assert(Object.values(controls).every(control=>control.value===''));
console.log('PASS explicit geography grouping, formats, conjunctions and control state');
