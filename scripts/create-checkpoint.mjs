#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const args = parseArgs(process.argv.slice(2));
const today = new Date().toISOString().slice(0, 10);
const month = today.slice(0, 7);

const owner = args.owner || process.env.USER || 'unknown';
const workstream = args.workstream || detectWorkstream() || 'unassigned-workstream';
const scope = args.scope || detectScope() || '全项目';
const reason = args.reason || '任务未完成，需要保存中间态以便后续恢复。';
const title = args.title || `${today} ${workstream} 断点快照`;
const slug = args.slug || `${today}-${workstream}-${owner}`.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
const outputDir = path.join(root, 'docs/08-progress/checkpoints', month);
const outputFile = path.join(outputDir, `${slug}.md`);

function parseArgs(raw) {
  const result = {};
  for (let i = 0; i < raw.length; i += 1) {
    const current = raw[i];
    if (!current.startsWith('--')) continue;
    const key = current.slice(2);
    const next = raw[i + 1];
    if (!next || next.startsWith('--')) {
      result[key] = true;
    } else {
      result[key] = next;
      i += 1;
    }
  }
  return result;
}

function runGit(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trimEnd();
  } catch {
    return '';
  }
}

function listMarkdown(dir) {
  if (!fs.existsSync(dir)) return [];
  const result = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...listMarkdown(full));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      result.push(full);
    }
  }
  return result;
}

function detectWorkstream() {
  const workstreamDir = path.join(root, 'docs/08-progress/workstreams');
  const files = listMarkdown(workstreamDir)
    .filter((file) => path.basename(file) !== 'README.md')
    .map((file) => path.basename(file, '.md'));
  return files.length === 1 ? files[0] : '';
}

function detectScope() {
  const changed = changedFiles();
  const scopes = [];
  if (changed.some((file) => file.startsWith('backend/'))) scopes.push('后端');
  if (changed.some((file) => file.startsWith('admin-web/'))) scopes.push('管理端');
  if (changed.some((file) => file.startsWith('student-web/'))) scopes.push('学生端');
  if (changed.some((file) => file.startsWith('miniprogram/'))) scopes.push('微信小程序');
  if (changed.some((file) => file.startsWith('docs/'))) scopes.push('文档');
  return scopes.join('、');
}

function changedFiles() {
  const status = runGit(['status', '--short']);
  if (!status) return [];
  return status.split('\n')
    .map((line) => line.slice(3).trim())
    .map((line) => line.includes(' -> ') ? line.split(' -> ').pop() : line)
    .filter(Boolean);
}

function formatList(items, fallback = '暂无') {
  if (!items.length) return `- ${fallback}`;
  return items.map((item) => `- ${item}`).join('\n');
}

function recentModifiedDocs() {
  return changedFiles().filter((file) => file.startsWith('docs/') && file.endsWith('.md'));
}

function packageScripts() {
  const packageFile = path.join(root, 'package.json');
  if (!fs.existsSync(packageFile)) return [];
  try {
    const json = JSON.parse(fs.readFileSync(packageFile, 'utf8'));
    return Object.keys(json.scripts || {}).map((name) => `npm run ${name}`);
  } catch {
    return [];
  }
}

function suggestedCommands() {
  const commands = [];
  if (fs.existsSync(path.join(root, 'backend/pytest.ini')) || fs.existsSync(path.join(root, 'backend/tests'))) {
    commands.push('cd backend && pytest -q');
  }
  if (fs.existsSync(path.join(root, 'admin-web/package.json'))) {
    commands.push('cd admin-web && npm run build');
  }
  if (fs.existsSync(path.join(root, 'student-web/package.json'))) {
    commands.push('cd student-web && npm run build');
  }
  commands.push(...packageScripts().filter((command) => command.includes('docs')));
  return [...new Set(commands)];
}

const branch = runGit(['branch', '--show-current']) || '未知';
const commit = runGit(['rev-parse', '--short', 'HEAD']) || '未知';
const diffStat = runGit(['diff', '--stat']) || '无未暂存 diff';
const stagedDiffStat = runGit(['diff', '--cached', '--stat']) || '无已暂存 diff';
const recentCommits = runGit(['log', '--oneline', '-5']).split('\n').filter(Boolean);
const files = changedFiles();

const content = `# ${title}

> 状态：当前
> 范围：${scope}
> 更新：${today}
> 工作流：${workstream}
> 负责人：${owner}
> 处理状态：open

## 中断原因

${reason}

## 本次目标

由模型根据当前对话补充：本次原本要完成什么，以及完成标准是什么。

## 已完成

由模型根据当前对话补充：已经阅读、修改、验证或确认了什么。

## 未完成

由模型根据当前对话补充：还没完成什么，哪些判断仍需确认。

## 当前现场

### 自动采集

- 分支：${branch}
- 当前提交：${commit}
- 工作流：${workstream}
- 负责人：${owner}
- 相关范围：${scope}

### 变更文件

${formatList(files)}

### 最近修改文档

${formatList(recentModifiedDocs())}

### Diff 统计

\`\`\`text
${diffStat}
\`\`\`

### 暂存区 Diff 统计

\`\`\`text
${stagedDiffStat}
\`\`\`

### 最近提交

${formatList(recentCommits)}

## 风险与阻塞

由模型根据当前对话补充：当前风险、阻塞点、不要重复探索的路径。

## 下一步

1. 由模型补充：恢复时先读什么。
2. 由模型补充：恢复时先执行什么。
3. 由模型补充：恢复时先验证什么。

## 建议验证命令

${formatList(suggestedCommands())}

## 关联文档

- \`docs/08-progress/workstreams/${workstream}.md\`
- \`docs/08-progress/project-status.md\`
`;

if (args['dry-run']) {
  process.stdout.write(content);
} else {
  fs.mkdirSync(outputDir, { recursive: true });
  if (fs.existsSync(outputFile) && !args.force) {
    console.error(`checkpoint 已存在：${path.relative(root, outputFile)}`);
    console.error('如需覆盖，请增加 --force');
    process.exit(1);
  }
  fs.writeFileSync(outputFile, content);
  console.log(`创建 checkpoint：${path.relative(root, outputFile)}`);
  console.log('下一步：请让模型补齐“本次目标 / 已完成 / 未完成 / 风险与阻塞 / 下一步”。');
}
