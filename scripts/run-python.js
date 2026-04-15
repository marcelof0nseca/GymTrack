const { existsSync } = require('fs');
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
const result = spawnSync(pythonExecutable, process.argv.slice(2), { stdio: 'inherit' });

process.exit(result.status === null ? 1 : result.status);
