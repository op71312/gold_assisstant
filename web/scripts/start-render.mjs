import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const standaloneDir = fileURLToPath(new URL('../.next/standalone/', import.meta.url));
const server = spawn(process.execPath, ['server.js'], {
  cwd: standaloneDir,
  env: process.env,
  stdio: 'inherit',
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    if (!server.killed) server.kill(signal);
  });
}

process.exitCode = await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.once('exit', (code) => resolve(code ?? 1));
});
