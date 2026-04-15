const { spawn } = require('child_process');
const { join } = require('path');

const env = { ...process.env };
delete env.ELECTRON_RUN_AS_NODE;

const cypressCli = join(process.cwd(), 'node_modules', 'cypress', 'bin', 'cypress');
const child = spawn(process.execPath, [cypressCli, ...process.argv.slice(2)], {
  stdio: 'inherit',
  env,
});

child.on('close', (code) => {
  process.exit(code === null ? 1 : code);
});
