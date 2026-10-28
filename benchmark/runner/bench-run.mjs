// bench-run.mjs - 并行评测矩阵（每块 repeat 次，分批并行）
// 用法: node runner/bench-run.mjs [--tasks t1,t2] [--models ds,mimo] [--minds nomind,mind] [--repeat 2] [--batch 6]
import { spawn } from "child_process";
import { writeFileSync, mkdirSync } from "fs";

const arg = n => { const i = process.argv.indexOf("--" + n); return i >= 0 ? process.argv[i+1] : null; };
const MODELS = [
  { key: "ds",   provider: "deepseek", model: "deepseek-v4-flash" },
  { key: "mimo", provider: "xiaomi",   model: "mimo-v2.5-pro" },
];
const MINDS = [
  { key: "nomind", val: "none" },
  { key: "mind",   val: "mind-context.txt" },
];
const ALL_TASKS = ["t1-data-loss","t2-config-parse","t3-scheduler","t4-statemachine","t5-renderer"];
const ROUNDS = { "t1-data-loss":3,"t2-config-parse":3,"t3-scheduler":3,"t4-statemachine":3,"t5-renderer":3 };
const tasks = (arg("tasks") || ALL_TASKS.join(",")).split(",");
const models = MODELS.filter(m => (arg("models") || "ds,mimo").split(",").includes(m.key));
const minds = MINDS.filter(m => (arg("minds") || "nomind,mind").split(",").includes(m.key));
const repeat = parseInt(arg("repeat") || "2");
const batch = parseInt(arg("batch") || "6");

const runId = new Date().toISOString().slice(0,16).replace(/[:T]/g,"-");
const dir = "results/" + runId; mkdirSync(dir, { recursive: true });

const jobs = [];
for (const t of tasks) for (const m of models) for (const mind of minds) for (let r=0; r<repeat; r++)
  jobs.push({ t, m, mind, tag: t + "/" + m.key + "/" + mind.key + "#" + (r+1) });

function runJob(job) {
  return new Promise(resolve => {
    const tracePath = dir + "/trace-" + job.tag.replace(/[\/#]/g, "-") + ".jsonl";
    const child = spawn("node", ["runner/task-runner.mjs", "--task", "tasks/" + job.t, "--provider", job.m.provider, "--model", job.m.model, "--mind", job.mind.val, "--rounds", String(ROUNDS[job.t]), "--trace", tracePath], { stdio: ["ignore","pipe","pipe"] });
    let out = "";
    child.stdout.on("data", d => out += d);
    child.stderr.on("data", d => process.stderr.write("[stderr] " + d.toString().slice(0,80)));
    child.on("close", () => {
      const line = out.trim().split("\n").filter(l => l.startsWith("{")).pop();
      try {
        const r = JSON.parse(line);
        resolve({ task: job.t, model: job.m.key, mind: job.mind.key, done: !!r.done, completedRound: r.completedRound, bizOk: !!r.bizOk, usage: r.usage, toolCmds: r.toolCmds || [], tag: job.tag });
      } catch (e) {
        resolve({ task: job.t, model: job.m.key, mind: job.mind.key, done: false, completedRound: 0, bizOk: false, error: "parse:" + String(e).slice(0,80), usage: null, toolCmds: [], tag: job.tag });
      }
    });
    child.on("error", e => resolve({ task: job.t, model: job.m.key, mind: job.mind.key, done: false, completedRound: 0, bizOk: false, error: String(e).slice(0,80), usage: null, toolCmds: [], tag: job.tag }));
  });
}

(async () => {
  const results = [];
  const start = Date.now();
  for (let i = 0; i < jobs.length; i += batch) {
    const batchJobs = jobs.slice(i, i + batch);
    const batchRes = await Promise.all(batchJobs.map(runJob));
    results.push(...batchRes);
    process.stderr.write("\n[batch] " + (i+batchRes.length) + "/" + jobs.length + " done, " + ((Date.now()-start)/1000).toFixed(0) + "s\n");
  }
  writeFileSync(dir + "/results.json", JSON.stringify(results, null, 2));
  writeFileSync(dir + "/trace.json", JSON.stringify(results.filter(r => r.toolCmds.length), null, 2));
  console.log(JSON.stringify({ runId, total: results.length, minutes: ((Date.now()-start)/60000).toFixed(1) }));
})();
