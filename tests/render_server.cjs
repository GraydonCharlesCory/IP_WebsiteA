/* Shared isolated loopback fixture, including a real populated-v3 upgrade path. */
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const path = require('node:path');
module.exports = async function startServer(scratch, legacy=false) {
  const script = `import sys
from pathlib import Path
from server.config import Settings
from server.setup import prepare_data
from server.app import make_server
s=Settings(data_dir=Path(sys.argv[1]))
if sys.argv[2]=='enrichment':
    from tests.enrichment_fixture import populated_fixture
    populated_fixture(s)
if sys.argv[2]=='legacy':
    from server import db
    from server.migration import add_columns
    from server.seed import seed
    from server.seed_v3 import seed_v3
    s.data_dir.mkdir(parents=True)
    with db.connect(s.db_path) as conn:
        for file in sorted(db.SCHEMA_DIR.glob('0[1-5]*.sql')):
            conn.executescript(file.read_text())
        add_columns(conn)
        seed(conn,s.clips_dir)
        seed_v3(conn)
        conn.execute('PRAGMA user_version=3')
        conn.commit()
prepare_data(s)
h=make_server(s,0)
print(h.server_port,flush=True)
h.serve_forever()`;
  const mode=legacy===true?'legacy':legacy||'fresh';
  const server=spawn('python3',['-u','-c',script,path.join(scratch,'data'),mode],{stdio:['ignore','pipe','pipe']});
  let errors='';server.stderr.on('data',data=>{errors+=data;});
  const stop=async()=>{server.kill('SIGTERM');if(server.exitCode===null) await once(server,'exit');};
  try {
    const port=await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error('Isolated server did not start: '+errors)),30000);
      const fail=message=>{clearTimeout(timer);reject(new Error(message+': '+errors));};
      server.once('error',error=>fail(error.message));server.once('exit',code=>fail('Isolated server exited '+code));
      server.stdout.once('data',data=>{clearTimeout(timer);resolve(Number(String(data).trim()));});
    });
    if(!(port>0)) throw new Error('Isolated server returned invalid port: '+port);
    return {base:`http://127.0.0.1:${port}`,stop};
  } catch(error) {await stop();throw error;}
};
