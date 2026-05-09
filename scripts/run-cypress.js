const { spawn } = require('child_process');
const { join } = require('path');

const env = { ...process.env };
delete env.ELECTRON_RUN_AS_NODE;

if (process.platform === 'win32') {
  const system32 = 'C:\\Windows\\System32';
  const currentPath = env.Path || env.PATH || '';

  if (!currentPath.toLowerCase().split(';').includes(system32.toLowerCase())) {
    const updatedPath = currentPath ? `${system32};${currentPath}` : system32;
    env.Path = updatedPath;
    env.PATH = updatedPath;
  }
}

const cypressCli = join(process.cwd(), 'node_modules', 'cypress', 'bin', 'cypress');
const child = spawn(process.execPath, [cypressCli, ...process.argv.slice(2)], {
  stdio: 'inherit',
  env,
});

child.on('close', (code) => {
  process.exit(code === null ? 1 : code);
});
