const { existsSync, mkdirSync, chmodSync } = require('fs');
const { tmpdir } = require('os');
const { join } = require('path');
const { spawnSync } = require('child_process');

const cwd = process.cwd();
const candidates = [
  join(cwd, 'venv', 'Scripts', 'python.exe'),
  join(cwd, '.venv', 'Scripts', 'python.exe'),
  join(cwd, 'venv', 'bin', 'python'),
  join(cwd, '.venv', 'bin', 'python'),
  'python',
];

const pythonExecutable = candidates.find((candidate) => candidate === 'python' || existsSync(candidate));
const tempDirectory = join(tmpdir(), 'gymtrack-cypress');
const dbDirectory = tempDirectory;
const dbPath = process.env.GYMTRACK_DB_PATH || join(dbDirectory, 'cypress-demo.sqlite3');

mkdirSync(dbDirectory, { recursive: true });

try {
  chmodSync(dbDirectory, 0o777);
} catch (_) {
  // Ignora erro de permissao em plataformas que nao aplicam chmod da mesma forma.
}

if (existsSync(dbPath)) {
  try {
    chmodSync(dbPath, 0o666);
  } catch (_) {
    // Ignora erro se o SO nao aplicar chmod diretamente.
  }
}

if (process.platform === 'win32' && existsSync(dbPath)) {
  spawnSync('C:\\Windows\\System32\\cmd.exe', ['/c', 'attrib', '-R', dbPath], { stdio: 'ignore' });
}

const env = {
  ...process.env,
  GYMTRACK_DB_PATH: dbPath,
};

const result = spawnSync(pythonExecutable, process.argv.slice(2), {
  stdio: 'inherit',
  env,
});

process.exit(result.status === null ? 1 : result.status);
