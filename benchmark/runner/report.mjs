// report.mjs - 从 results.json 生成得分表（完成 + 成本两维度）
import { readFileSync, writeFileSync } from "fs";

const runId = process.argv[2];
const results = JSON.parse(readFileSync("results/" + runId + "/results.json", "utf8"));

// 价格（元/M token）: v4f 峰/谷；mimo 单
const HIT_RATE = 0.99; // 用户日常缓存命中率（98.5-99.2%，取99%）
const PRICE = {
  ds:   { peak: { in: 3.0, out: 9.0, cache: 0.10 }, valley: { in: 1.5, out: 4.5, cache: 0.05 } },
  mimo: { single: { in: 3.11, out: 6.22, cache: 0.026 } },
};

function costOf(r) {
  if (!r.usage || !r.usage.totalTokens) return null;
  const u = r.usage, p = PRICE[r.model];
  // 预估价格：保留未命中输入+输出实际值；命中输入 = 未命中 × HIT/(1-HIT) 反算
  const hit = u.input * (HIT_RATE / (1 - HIT_RATE));
  if (p.single) {
    const c = (u.input/1e6)*p.single.in + (hit/1e6)*p.single.cache + (u.output/1e6)*p.single.out;
    return { single: c };
  }
  const peak = (u.input/1e6)*p.peak.in + (hit/1e6)*p.peak.cache + (u.output/1e6)*p.peak.out;
  const valley = (u.input/1e6)*p.valley.in + (hit/1e6)*p.valley.cache + (u.output/1e6)*p.valley.out;
  return { peak, valley };
}

let lines = ["# MIND 评测得分表（完成 + 成本两维度）", "", "| 任务 | 模型 | 无MIND | 有MIND | 增益 | 无MIND成本(¥) | 有MIND成本(¥) |", "|---|---|---|---|---|---|---|"];
const csv = ["task,model,mind,done,completedRound,totalTokens,cost"];
const groups = {};
for (const r of results) {
  const c = costOf(r);
  const costStr = c ? (c.single ? c.single.toFixed(2) : "峰" + c.peak.toFixed(2) + "/谷" + c.valley.toFixed(2)) : "-";
  csv.push([r.task, r.model, r.mind, r.done, r.completedRound, r.usage?.totalTokens||0, costStr].join(","));
  const k = r.task + "|" + r.model;
  (groups[k] = groups[k] || []).push(r);
}
for (const k of Object.keys(groups).sort()) {
  const [task, model] = k.split("|");
  const no = groups[k].find(r => r.mind === "nomind");
  const yes = groups[k].find(r => r.mind === "mind");
  const fmt = r => r.done ? "✓" + r.completedRound + "轮" : "✗" + (r.error ? "超时" : r.completedRound + "轮");
  let gain = "-";
  if (yes && no) {
    if (yes.done !== no.done) gain = yes.done ? "✓完成" : "✗失败";
    else if (yes.completedRound < no.completedRound) gain = "轮数快";
    else gain = "=";
  }
  const cfmt = r => { const c = costOf(r); return c ? (c.single ? "¥" + c.single.toFixed(2) : "¥" + c.peak.toFixed(2) + "/" + c.valley.toFixed(2)) : "-"; };
  lines.push("| " + task + " | " + model + " | " + (no ? fmt(no) : "-") + " | " + (yes ? fmt(yes) : "-") + " | " + gain + " | " + (no ? cfmt(no) : "-") + " | " + (yes ? cfmt(yes) : "-") + " |");
}
writeFileSync("results/" + runId + "/score.md", lines.join("\n"));
writeFileSync("results/" + runId + "/score.csv", csv.join("\n"));
console.log(lines.join("\n"));
