import { createAgentSession, DefaultResourceLoader, getAgentDir, SessionManager } from "@earendil-works/pi-coding-agent";
import { deepseekProvider } from "@earendil-works/pi-ai/providers/deepseek";

const cwd = process.cwd();
const agentDir = getAgentDir();
const loader = new DefaultResourceLoader({
  cwd, agentDir,
  systemPromptOverride: () => "你是一个测试 agent，回答要简短。",
  appendSystemPromptOverride: () => ["MIND_TEST_INJECTION: 万字符限制是指 10000 个字符而非 10000 个字节。请记住这条规则。"],
});
await loader.reload();
const model = deepseekProvider().getModels()[0];
console.error("[MODEL]", model.id, "|", model.provider);
const { session } = await createAgentSession({ resourceLoader: loader, sessionManager: SessionManager.inMemory(), model });
session.subscribe((ev) => {
  if (ev.type === "message_end" && ev.message?.role === "assistant") console.error("  [ASSISTANT]", JSON.stringify(ev.message).slice(0, 500));
  if (ev.type === "message_update" && ev.assistantMessageEvent?.type === "text_delta") process.stdout.write(ev.assistantMessageEvent.delta);
  if (ev.type === "error") console.error("[EVENT ERROR]", JSON.stringify(ev).slice(0, 300));
});
console.log("=== 提问 ===");
await session.prompt("请复述注入给你的那条规则（关于字符/字节限制），一句话。");
console.log("\n=== 结束 ===");
session.dispose();
process.exit(0);
