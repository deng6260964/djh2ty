#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const root = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();
const progressDir = path.join(root, 'docs/08-progress');
const workstreamDir = path.join(progressDir, 'workstreams');
const checkpointDir = path.join(progressDir, 'checkpoints');
const maxOpenDays = Number(process.env.CHECKPOINT_MAX_OPEN_DAYS || 14);

const errors = [];
const warnings = [];

function walk(dir, result = []) {
  if (!fs.existsSync(dir)) return result;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, result);
    if (entry.isFile() && entry.name.endsWith('.md')) result.push(full);
  }
  return result;
}

function rel(file) {
  return path.relative(root, file).split(path.sep).join('/');
}

function read(file) {
  return fs.readFileSync(file, 'utf8');
}

function meta(text, key) {
  return text.split(/\r?\n/).slice(0, 12).join('\n').match(new RegExp(`^> ${key}：(.+)$`, 'm'))?.[1]?.trim() || '';
}

function daysSince(dateText) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateText)) return 0;
  const start = new Date(`${dateText}T00:00:00Z`);
  const now = new Date();
  return Math.floor((now - start) / 86400000);
}

if (!fs.existsSync(progressDir)) {
  warnings.push('未发现 docs/08-progress/，跳过进度检查。');
} else {
  const workstreams = new Set(
    walk(workstreamDir)
      .filter((file) => path.basename(file) !== 'README.md')
      .map((file) => path.basename(file, '.md'))
  );

  const projectStatus = path.join(progressDir, 'project-status.md');
  if (!fs.existsSync(projectStatus)) {
    errors.push('缺少进度总览：docs/08-progress/project-status.md');
  }

  const openByWorkstream = new Map();
  for (const file of walk(checkpointDir).filter((item) => path.basename(item) !== 'README.md')) {
    const text = read(file);
    const status = meta(text, '状态');
    const scope = meta(text, '范围');
    const updated = meta(text, '更新');
    const workstream = meta(text, '工作流');
    const checkpointStatus = meta(text, '处理状态') || 'open';

    if (!status || !scope || !updated) {
      errors.push(`checkpoint 缺少标准状态块：${rel(file)}`);
    }
    if (!workstream) {
      errors.push(`checkpoint 缺少工作流字段：${rel(file)}`);
    } else if (workstream !== 'unassigned-workstream' && !workstreams.has(workstream)) {
      errors.push(`checkpoint 引用了不存在的工作流：${rel(file)} -> ${workstream}`);
    }
    if (!['open', 'resumed', 'closed', 'archived'].includes(checkpointStatus)) {
      errors.push(`checkpoint 处理状态不合法：${rel(file)} -> ${checkpointStatus}`);
    }
    if (checkpointStatus === 'open') {
      const list = openByWorkstream.get(workstream) || [];
      list.push(file);
      openByWorkstream.set(workstream, list);
      const age = daysSince(updated);
      if (age > maxOpenDays) {
        warnings.push(`checkpoint open 超过 ${maxOpenDays} 天：${rel(file)}，已 ${age} 天`);
      }
    }
  }

  for (const [workstream, files] of openByWorkstream.entries()) {
    if (workstream && files.length > 1) {
      warnings.push(`工作流存在多个 open checkpoint：${workstream} (${files.map(rel).join(', ')})`);
    }
  }
}

for (const warning of warnings) {
  console.warn(`警告：${warning}`);
}

if (errors.length > 0) {
  for (const error of errors) {
    console.error(`错误：${error}`);
  }
  console.error(`\n进度检查失败：${errors.length} 个错误，${warnings.length} 个警告`);
  process.exit(1);
}

console.log(`进度检查通过：${warnings.length} 个警告`);
