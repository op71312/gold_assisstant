import { cpSync, mkdirSync } from 'node:fs';

mkdirSync('.next/standalone/.next', { recursive: true });
cpSync('.next/static', '.next/standalone/.next/static', { recursive: true });
cpSync('public', '.next/standalone/public', { recursive: true });
cpSync('data', '.next/standalone/data', { recursive: true });
