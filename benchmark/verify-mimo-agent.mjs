import { createAgentSession, DefaultResourceLoader, getAgentDir, SessionManager } from "@earendil-works/pi-coding-agent";
import { xiaomiProvider } from "@earendil-works/pi-ai/providers/xiaomi";

const model = xiaomiProvider().getModels().find(m => m.id === "mimo-v2.5-pro");
console.log("[MODEL]", model?.id, "|", model?.provider);
const cwd = process.cwd();
const loader = new DefaultResourceLoader({ cwd, agentDir: getAgentDir(), systemPromptOverride: () => "回答要简短。" });
await loader.reload();
const { session } = await createAgentSession({ resourceLoader: loader, sessionManager: SessionManager.inMemory(), model });
session.subscribe((ev) => {
  if (ev.type === "message_end" && ev.message?.role === "assistant") {
    const text = ev.message?.content?.filter?.(c => c.type === "text").map(c => c.text).join("");
    console.log("[MIMO 回复]", text?.slice(0, 100));
  }
  if (ev.type === "error") console.error("[ERROR]", JSON.stringify(ev).slice(0, 300));
});
await session.prompt("只回复两个字：通了");
session.dispose();
process.exit(0);
