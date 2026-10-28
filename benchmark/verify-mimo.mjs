import { xiaomiProvider } from "@earendil-works/pi-ai/providers/xiaomi";
const models = xiaomiProvider().getModels();
console.log("xiaomi 模型:", models.map(m => m.id).join(", "));
const model = models.find(m => m.id.includes("pro") || m.id.includes("2.5")) || models[0];
console.log("选用:", model.id);
// 最小连通测试：直接调 pi-ai（不经过 agent，最快验证 MIMO API）
import { createProvider } from "@earendil-works/pi-ai";
const provider = xiaomiProvider();
// 用 provider 的 auth 从 auth.json 解析（pi 系统）
console.log("provider:", provider.id, "| auth 已配:", !!provider.auth);
