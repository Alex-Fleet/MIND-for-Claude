// task-runner — 跑单个 {task, model, mindOn} 格
// 用法: node task-runner.mjs --task <dir> --provider <deepseek|xiaomi> --model <id> --mind <file|none> --rounds <N>
import { createAgentSession, DefaultResourceLoader, getAgentDir, SessionManager } from "@earendil-works/pi-coding-agent";
import { deepseekProvider } from "@earendil-works/pi-ai/providers/deepseek";
import { xiaomiProvider } from "@earendil-works/pi-ai/providers/xiaomi";
import { execSync } from "child_process";
import { readFileSync, existsSync, mkdtempSync, cpSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

function arg(name) {
  const i = process.argv.indexOf("--" + name);
  return i >= 0 ? process.argv[i + 1] : null;
}

const taskDir = join(process.cwd(), arg("task")), providerName = arg("provider"), modelId = arg("model");
const mindFile = arg("mind"), maxRounds = parseInt(arg("rounds") || "3");
const traceFile = arg("trace") ? join(process.cwd(), arg("trace")) : null;   // 绝对路径（chdir 沙箱后仍有效）
const task = JSON.parse(readFileSync(join(taskDir, "task.json"), "utf8"));

// 模型
const provider = providerName === "deepseek" ? deepseekProvider() : xiaomiProvider();
const model = provider.getModels().find(m => m.id === modelId) || provider.getModels()[0];

// MIND 注入
const inject = mindFile !== "none" && existsSync(mindFile)
  ? ["[MIND 全局记忆]\n" + readFileSync(mindFile, "utf8")]
  : ["（评测用通用提示，非特定记忆）"];

// 沙箱：只给 agent 任务源码（src/），不给测试/任务配置——agent 自己琢磨，测试由框架判定
const workDir = mkdtempSync(join(tmpdir(), "bench-"));
cpSync(join(taskDir, "src"), join(workDir, "src"), { recursive: true, filter: (s) => !s.includes("__pycache__") });
process.chdir(workDir);   // 强制 agent 工具（Bash/文件）cwd 指向沙箱副本，禁碰宿主

const loader = new DefaultResourceLoader({
  cwd: workDir, agentDir: getAgentDir(),
  systemPromptOverride: () => "你是评测环境中的编程 agent。用户会给你任务和检查点反馈，认真完成任务。回答中文。",
  appendSystemPromptOverride: () => inject,
});
await loader.reload();
const { session } = await createAgentSession({ resourceLoader: loader, sessionManager: SessionManager.inMemory(), model });

function extractFailed(out) {
  // 从 pytest 输出提取失败测试名（黑盒反馈用，不给测试代码）
  const failed = [];
  for (const line of String(out).split("\n")) {
    const m = line.match(/FAILED [^:]+::([^\s]+)/);
    if (m) failed.push(m[1].replace("test_", "").replace(/_/g, " "));
  }
  return failed;
}

function runCheck(cmd) {
  // 组合测试区：宿主 tests + 沙箱 agent 修改后的 src（agent 看不到 tests）
  const checkDir = mkdtempSync(join(tmpdir(), "bench-check-"));
  cpSync(join(taskDir, "tests"), join(checkDir, "tests"), { recursive: true });
  cpSync(join(workDir, "src"), join(checkDir, "src"), { recursive: true });
  try {
    const out = execSync(`cd "${checkDir}" && ${cmd}`, { timeout: 60000, stdio: "pipe" }).toString();
    return { ok: true, out: out.slice(-400), failed: extractFailed(out) };
  } catch (e) {
    const out = String(e.stdout || e.message);
    return { ok: false, out: out.slice(-400), failed: extractFailed(out) };
  } finally {
    rmSync(checkDir, { recursive: true, force: true });
  }
}

let done = false, completedRound = 0, lastBiz = null, lastFailed = null;
const usage = { input:0, output:0, cacheRead:0, cacheWrite:0, totalTokens:0 };
session.subscribe((ev) => { if (ev.type === "message_end" && ev.message?.usage) { const u = ev.message.usage; usage.input += u.input||0; usage.output += u.output||0; usage.cacheRead += u.cacheRead||0; usage.cacheWrite += u.cacheWrite||0; usage.totalTokens += u.totalTokens||0; } });
const toolCmds = [];
session.subscribe((ev) => { if (ev.type && (ev.type.includes("tool") || ev.type.includes("execution"))) { const c = ev.command || ev.input || (ev.event?.command) || (ev.message?.content?.[0]?.text); if (typeof c === "string" && c.length < 200) toolCmds.push(c); } });

// 完整轨迹记录：结构化提取（思考/消息/工具），JSON 可解析不截断
function summarizeEv(ev) {
  const msg = ev.message || ev.assistantMessageEvent?.partial || {};
  const content = Array.isArray(msg.content) ? msg.content : [];
  const parts = content.map(c => {
    if (typeof c === "string") return c;
    if (c.type === "thinking") return `[think] ${(c.thinking || c.content || "").slice(0, 400)}`;
    if (c.type === "tool_use") return `[use ${c.name}] ${JSON.stringify(c.input || {}).slice(0, 300)}`;
    if (c.type === "tool_result") return `[result] ${String(c.content || "").slice(0, 300)}`;
    return (c.text || c.type || "").slice(0, 300);
  }).join(" | ").slice(0, 2500);
  return {
    t: ev.type,
    toolName: ev.toolName,
    filePath: ev.args?.filePath,
    command: ev.args?.command,
    text: parts || undefined,
  };
}
const trace = [];
session.subscribe((ev) => { if (traceFile) trace.push(JSON.stringify(summarizeEv(ev))); });
for (let r = 1; r <= maxRounds && !done; r++) {
  // 每轮提示 = 任务描述/hint + 上一轮的验收测试黑盒反馈（不给测试代码）
  const base = r === 1 ? task.description : (task["hint_round" + (r - 1)] || "检查点未通过，请继续修复。");
  let msg = base;
  if (r > 1 && lastFailed && lastFailed.length > 0) {
    msg += "\n[验收反馈] 还有 " + lastFailed.length + " 个验收场景未通过：" + lastFailed.join("、") + "。请继续修复（验收测试你看不到，以你的代码逻辑为准）。";
  } else if (r > 1 && lastBiz?.ok) {
    msg += "\n[验收反馈] 验收测试已通过，请确保没破坏其他功能。";
  }
  console.error(`[R${r}] 发送: ${msg.slice(0, 60)}...`);
  await session.prompt(msg);

  lastBiz = runCheck(task.check_biz);
  lastFailed = lastBiz?.failed || [];
  let reg = null;
  if (lastBiz.ok) reg = runCheck(task.check_regress);

  if (lastBiz.ok && reg?.ok) { done = true; completedRound = r; }
}

console.log(JSON.stringify({
  task: task.id, provider: providerName, model: model.id, mind: mindFile !== "none",
  done, completedRound, bizOk: lastBiz?.ok ?? false, usage, toolCmds,
}));
session.dispose();
if (traceFile && trace.length) writeFileSync(traceFile, trace.join("\n") + "\n", "utf8");
rmSync(workDir, { recursive: true, force: true });   // 清理沙箱副本
process.exit(0);
