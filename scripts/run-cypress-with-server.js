const { spawn } = require('child_process');
const http = require('http');
const https = require('https');
const { join } = require('path');

const baseUrl = process.env.CYPRESS_baseUrl || 'http://127.0.0.1:8000';
const serverHost = baseUrl.replace(/^https?:\/\//, '');
const healthcheckUrl = `${baseUrl.replace(/\/$/, '')}/register/`;
const cypressScript = join(process.cwd(), 'scripts', 'run-cypress.js');
const pythonScript = join(process.cwd(), 'scripts', 'run-python-e2e.js');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ping(url) {
  return new Promise((resolve) => {
    const client = url.startsWith('https://') ? https : http;
    const request = client.get(url, (response) => {
      response.resume();
      resolve(response.statusCode && response.statusCode < 500);
    });

    request.on('error', () => resolve(false));
    request.setTimeout(3000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function waitForServer(url, timeoutMs = 60000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    if (await ping(url)) {
      return;
    }

    await sleep(1000);
  }

  throw new Error(`Servidor nao respondeu em ${url} dentro de ${timeoutMs / 1000}s.`);
}

function runPythonCommand(args) {
  return new Promise((resolve, reject) => {
    const child = spawn('node', [pythonScript, 'manage.py', ...args], {
      stdio: 'inherit',
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(`Falha ao executar python manage.py ${args.join(' ')}.`));
    });

    child.on('error', reject);
  });
}

function stopProcessTree(child) {
  return new Promise((resolve) => {
    if (!child || child.killed) {
      resolve();
      return;
    }

    if (process.platform === 'win32') {
      const killer = spawn('C:\\Windows\\System32\\taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], {
        stdio: 'ignore',
      });
      killer.on('close', () => resolve());
      killer.on('error', () => resolve());
      return;
    }

    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch (_) {
      // Ignora erro se o processo ja tiver terminado.
    }

    resolve();
  });
}

async function main() {
  let server;
  let exitCode = 1;

  try {
    await runPythonCommand(['migrate']);
    await runPythonCommand(['popular_exercicios']);

    server = spawn('node', ['scripts/run-python-e2e.js', 'manage.py', 'runserver', serverHost], {
      stdio: 'inherit',
      detached: process.platform !== 'win32',
    });

    await waitForServer(healthcheckUrl);

    exitCode = await new Promise((resolve, reject) => {
      const env = { ...process.env, CYPRESS_baseUrl: baseUrl };
      const cypress = spawn(process.execPath, [cypressScript, 'run', '--e2e', '--browser', 'chrome'], {
        stdio: 'inherit',
        env,
      });

      cypress.on('close', (code) => resolve(code === null ? 1 : code));
      cypress.on('error', reject);
    });
  } catch (error) {
    console.error(error.message);
  } finally {
    await stopProcessTree(server);
  }

  process.exit(exitCode);
}

main();
