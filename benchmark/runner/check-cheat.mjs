// check-cheat.mjs - 防作弊检查：从 trace.json 检查 agent 是否访问工作区外
// 用法: node runner/check-cheat.mjs <runId>
import { readFileSync, existsSync } from "fs";

const runId = process.argv[2];
const trace = `results/${runId}/trace.json`;
if (!existsSync(trace)) { console.log("无 trace.json（或全部无工具调用）"); process.exit(0); }
const results = JSON.parse(readFileSync(trace, "utf8"));

// 工作区外特征: 原项目路径 / 主目录敏感路径 / 网络抓取
const SUSPECT = [
  { re: /(~|\$HOME)\//, label: "主目录" },
  { re: /\.claude\//, label: "~/.claude" },
  { re: /Documents\/Agent R&D\/(?!Memory Plugin\/benchmark\/tasks)/, label: "工作区外项目" },
  { re: /curl|wget|https?:\/\//, label: "联网抓取" },
  { re: /(OASIS|GOAI|KG Kernal|study assistant)/, label: "其他项目名" },
];

let flagged = 0;
for (const r of results) {
  for (const cmd of r.toolCmds || []) {
    for (const s of SUSPECT) {
      if (s.re.test(cmd)) {
        console.log(`[作弊嫌疑] ${r.tag}: ${s.label} → ${cmd.slice(0,80)}`);
        flagged++; break;
      }
    }
  }
}
console.log(flagged === 0 ? "✓ 未发现工作区外访问" : `⚠ 发现 ${flagged} 条嫌疑`);
