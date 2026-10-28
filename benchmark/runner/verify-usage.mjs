// 验证 pi 每轮 usage 是否被 message_end 完整记录
import { createAgentSession, DefaultResourceLoader, getAgentDir, SessionManager } from "@earendil-works/pi-coding-agent";
import { deepseekProvider } from "@earendil-works/pi-ai/providers/deepseek";

const model = deepseekProvider().getModels()[0];
const loader = new DefaultResourceLoader({ cwd: process.cwd(), agentDir: getAgentDir(), systemPromptOverride: () => "你是评测中的编程 agent，认真完成任务。", });
await loader.reload();
const { session } = await createAgentSession({ resourceLoader: loader, sessionManager: SessionManager.inMemory(), model });

let rounds = 0; let sum = { input:0, output:0, cacheRead:0, totalTokens:0, cost:0 };
session.subscribe((ev) => {
  if (ev.type === "message_end" && ev.message?.usage) {
    rounds++;
    const u = ev.message.usage;
    sum.input += u.input||0; sum.output += u.output||0; sum.cacheRead += u.cacheRead||0; sum.totalTokens += u.totalTokens||0; sum.cost += u.cost?.total||0;
    console.error(`[msg_end ${rounds}] role=${ev.message.role} in=${u.input} cache=${u.cacheRead} out=${u.output} total=${u.totalTokens} cost=$${u.cost?.total?.toFixed(6)}`);
  }
  if (ev.type === "error") console.error("[EV-ERR]", JSON.stringify(ev).slice(0,200));
});
await session.prompt("查看 src/store.py 的内容，然后只回复：看完了");
console.log(JSON.stringify({ rounds, sum }));
session.dispose(); process.exit(0);
