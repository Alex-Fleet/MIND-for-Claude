import { createProvider } from "@earendil-works/pi-ai";
import { openAICompletionsApi } from "@earendil-works/pi-ai/api/openai-completions.lazy";

export default function (pi) {
  pi.registerProvider(createProvider({
    id: "deepseek",
    name: "DeepSeek",
    baseUrl: "https://api.deepseek.com",
    auth: {
      apiKey: {
        name: "DeepSeek API key",
        async login(interaction) {
          return { type: "api_key", key: await interaction.prompt({ type: "secret", message: "DeepSeek API key" }) };
        },
        async resolve() {
          const key = process.env.DS_API_KEY;
          return key ? { auth: { apiKey: key }, source: "env" } : undefined;
        }
      }
    },
    models: [
      { id: "deepseek-chat", name: "DS V4 Flash", reasoning: false, input: ["text"],
        cost: { input: 1, output: 2, cacheRead: 0.02, cacheWrite: 1 },
        contextWindow: 1000000, maxTokens: 8000 }
    ],
    api: openAICompletionsApi()
  }));
}
