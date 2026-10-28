# MIND 评测子模块 — 架构设计（AD）

> 配套：[PRD](docs/prd/mind-eval-benchmark.md) ｜ 版本：v0.2（已确认设计）

---

## 0. 整体观念（一句话）

> 用 pi agent 在 Docker 沙箱里模拟「用户与 agent 的多轮对话」，任务按难度分级给**机会次数**，每轮跑**业务+回归双层检查点**，任务难到多次 compact——测 MIND 记忆注入能否防信息丢失、让模型在更少机会内完成，产出「完成度 / 机会消耗 / 成本（v4f 峰谷双价）」得分表。

```
评测矩阵 {MIMO-v2.5-pro, ds-v4f} × {有MIND, 无MIND} × {5 难任务(A/B/C 分级)}
    │
    ▼ 每格（宿主调度）
┌───────────────────────────────────────────────┐
│ Docker 沙箱（独立工作区，只含任务精简代码，禁联网）│
│   pi session（多轮用户对话，机会次数 = 难度分级）  │
│   第1轮: 注入「任务描述(现象)」→ agent 执行       │
│      → 跑 业务测试 + 回归测试（双层）             │
│        都过 → 完成（记机会消耗=1）               │
│        任一不过 → 预设反馈第2轮 → agent 再执行     │
│      → …机会次数用尽 → 失败(未收敛)              │
│   期间 context 增长 → compact 压缩              │
│     有MIND: 记忆常驻 system prompt，压不丢       │
│     无MIND: 靠对话上下文，压一次丢一点            │
└───────────────────────────────────────────────┘
    │ 收集: 完成度 / 机会消耗 / token / 成本
    │     v4f: 输出峰价+谷价两个成本
    ▼
得分表文件（Markdown + CSV，含 MIND 增益 + 模型差异对比）
```

## 1. 实体与操作

| 实体 | 关键字段 | 操作 |
|---|---|---|
| **Task** | id、难度(A/B/C)、机会次数、任务描述(现象)、业务测试、回归测试、反馈序列 | 定义 / 校验 / 打包 |
| **ModelConfig** | provider、modelId、API key、定价(峰/谷) | 注册 / 读取 |
| **MindContext** | 注入内容（有MIND=全局记忆 / 无MIND=通用提示）| 生成 / 注入 |
| **Sandbox** | 镜像、工作区、容器 | 创建 / 运行 / 销毁 |
| **RunResult** | taskId、model、mindOn、完成度、机会消耗、token、成本(峰/谷)、耗时 | 收集 / 持久化 |
| **ScoreTable** | 矩阵汇总 + 增益对比 | 生成 / 落盘 |

## 2. 数据流

```
config(模型/任务/注入开关)
  → Runner 展开矩阵
  → 每格:
      Injector 生成追加提示（有/无 MIND）
      Sandbox 创建容器 + 挂载任务包
      容器内 TaskRunner:
        pi session → 注入追加内容
        for round in 1..机会次数(难度分级):
          prompt(任务描述 或 反馈[round]) → agent 执行
          跑 业务测试 + 回归测试（双层）
          都过 → break(完成)；否则反馈[round+1]
        记录 完成度/机会消耗/compact次数/token
      返回 RunResult → Sandbox 销毁
  → Collector → Report（得分表：含 v4f 峰谷成本）
```

## 3. 模块边界

```
宿主侧（Node/TS）                    容器侧（Node/TS）
┌────────────────────────────┐   ┌─────────────────────────────┐
│ runner   矩阵调度/生命周期    │ → │ task-runner 多轮对话执行器     │
│ injector MIND 注入生成       │   │   pi session + 注入           │
│ tasks    任务定义/打包        │   │   rounds(机会次数) + 双层检查点 │
│ sandbox  Docker 管理         │   │                             │
│ collector 结果收集           │   │   工作区（只含任务精简代码）    │
│ report   得分表生成          │   │                             │
└────────────────────────────┘   └─────────────────────────────┘
依赖单向；宿主不碰任务代码；容器不碰宿主配置（API key 经 env）
```

## 4. 接口（最小集）

| 接口 | 形态 | 说明 |
|---|---|---|
| 任务定义 | `tasks/<id>/task.json`（难度/机会次数/描述）+ `check_biz.sh` + `check_regress.sh` + `feedbacks.json` | 业务/回归分离的双检查点 |
| MIND 注入 | `injector.generate(mindOn) → string[]` | 追加 system prompt 片段 |
| 沙箱 | `sandbox.create(task) / run(cmd) / destroy()` | Docker 生命周期 |
| 任务执行 | `node run.mjs <task> <apiKey> <append> <maxRounds>` | 容器内执行，输出 JSON |
| 结果 | 每格 `RunResult` JSON → `results/<runId>/` | 含成本(峰/谷) |
| 报告 | `score-<runId>.md` + `.csv` | 矩阵 + 增益对比 |

## 5. 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| harness | `@earendil-works/pi-coding-agent` | agent loop + `appendSystemPromptOverride` 注入 |
| 语言 | Node.js/TypeScript（宿主+容器）| pi SDK 原生 |
| 沙箱 | Docker（`--network none`）| 隔离工作区 + 禁联网 |
| 结果存储 | 文件（JSON/Markdown/CSV）| 满足"落文件" |
| 矩阵 | 串行 | 8GB Mac 防 OOM |

## 6. 写时考虑

### 边界条件
- API key 缺失/无效 → 该格失败，不中断矩阵
- 单格超时（15min）→ 杀容器记超时；单轮超时（3min）→ 该轮失败进下轮
- compact 触发：任务须能触发 ≥2 次压缩（任务设计校验）
- 沙箱逃逸：`--network none` + 只挂任务包
- 成本失控：跑前预算，超预算中断
- 双层检查点：业务 + 回归都过才算完成（防"改对了但搞坏别的"）

### 验收标准
- runner：`bench-run --models X,Y --tasks all` 跑完无崩溃
- injector：有 MIND = 全局记忆；无 MIND = 通用提示（可审计）
- task-runner：单格跑通多轮 + 双层检查点 + 结果 JSON
- sandbox：容器创建/销毁正常，网络隔离生效
- report：得分表含 完成度/机会消耗/成本(峰谷) + 增益对比

### 技术风险
- pi 为 npm 包（镜像预装 Node）
- MIND 全量注入可能超 pi prompt 限制（注入前长度校验）
- 长任务 5 任务 × 机会次数 × 2 模型 token 消耗需监控

## 7. 待验证（实现时实测）

1. pi SDK 在容器内最小例子 + `appendSystemPromptOverride` 注入生效
2. MIND 全量注入长度是否在 pi 限制内
3. 每个任务实测触发 ≥2 次 compact（测出 MIND 防丢价值）
