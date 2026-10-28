# 全局规范迁移提案：去重、结构、OASIS 验证

> 日期：2026-10-20
> 状态：**提案，未应用**。两个 standard、`user-profile`、skill 均未改动。
> 范围：只处理全局长期层；项目级 turns / daily / monthly 后置。
> 关联：`memory/global/behavior-standards.md`、`memory/global/programming-standards.md`、`memory/global/user-profile.md`。

---

## 1. 结论摘要

- 原始候选 39 条；按用户要求删除「操作矩阵」后为 **38 条**。
- 去重结果：**9 条已有规范覆盖**、**10 条需改写/补语境**、**19 条真正新增**（其中 17 条进标准，2 条环境经验进 exps/user-profile）。
- **不新开 standard 文件**。新增规则按“做人/工作/思考”和“工程/代码”分别并入两个现有文件。
- **OASIS 拆三层**：规范层写不变量，skill 层放可执行代码，exps 层放踩坑；代码不塞进 standard。
- **环境事实不写死**。标准里写“检测习惯”，当前观测值放 `user-profile` 和本文 6.2 的带日期快照，随时可重测。
- 项目级迁移继续后置。

---

## 2. 去重分类

### 2.1 已有规范覆盖（9 条，不重复写）

| 候选 | 现有位置 |
|---|---|
| 用户铁律与偏好 | behavior 总纲 + ①–⑧ + CLAUDE.md |
| 没指令不碰代码 | behavior ⑦；本次拆成 ⑦-A/⑦-B |
| Git 版本管理 | programming Git / 版本号 |
| Git 分支工作流 | programming Git / branch |
| Changelog 独立文件 | programming 文档 |
| docs 体系与 issue 规范 | programming 文档 |
| 执行效率铁律 | behavior 子代理调研 + 环境故障停止 |
| 能复用就复用、低耦合 | programming 代码 / 低耦合高内聚 |
| MIND 看板 8765 | programming 端口 / 网络 |

### 2.2 需改写 / 补语境（10 条）

| 候选 | 落点 | 语境/写法 |
|---|---|---|
| 改 bug 先找用户 | behavior ⑦-A | 只针对任务之外的 bug；用户点名要修的照修，commit 仍走 ⑦-B |
| 破坏性操作先验目标 | behavior ⑦-B | kill/删除/覆盖/迁移先确认目标与范围；只读命令不适用 |
| 不甩锅缓存/用户 | behavior ⑤ | 修完仍不对、用户说“还是这样” → 先查渲染/代码/数据路径 |
| 审查子代理规范 | behavior ⑥ | 完整审查 vs 轻量验证；任务书写目标/死清单/范围/输出格式 |
| 小东西别套重审查 | behavior ⑥ | 无持久化的小 UI/文案/样式：构建 + 用户目测；不派重审查 |
| Sweep whole class | behavior ③ | 完成清单增加“同类入口全扫” |
| 测试复现真实失败路径 | programming 测试设计 | 回归测试以用户真实失败路径为输入 |
| 验证范围跟着改动走 | programming 测试设计 | 自动化用例仍全面；人验只覆盖改动路径，全量穷举先问 |
| 注释只讲现状 | programming 代码/可读 | 注释描述当前行为；历史/废弃路径单独标 |
| Never print config raw | programming 代码/安全 | 只取需要的字段；禁止整段打印 config |

### 2.3 真正新增（19 条）

其中 **17 条进 standard**：

| 候选 | 落点 |
|---|---|
| 用户顺手就开口 | behavior 工作方式 → 沟通 |
| 拿用户文件当输入先讲 | behavior 工作方式 → 调研/搜索 |
| 说开干 = 那批全做 | behavior 工作方式 → 沟通 |
| 用户截图自己找自己读 | behavior 工作方式 → 沟通 |
| 不注入无上限内容 | behavior 整体意识 → 资源边界 |
| No guessing data sizes | behavior ① 触发项 |
| 浏览器检查用轮询不用 sleep | programming 测试 → 浏览器/UI 验证 |
| 基准本身也要先验 | programming 测试设计 |
| 没参照不许调参数 | programming 代码/可维护 |
| 改前端必须重新构建 | programming 构建/前端构建一致性 |
| 私下口径 vs 可写内容（P0） | behavior 工作方式 → 交付写作 |
| 交付文档不写元信息与内部底稿（P0） | behavior 工作方式 → 交付写作 |
| headless 会漏真窗口渲染 bug | programming 测试 → 浏览器/UI 验证 |
| JS 页面用浏览器抓 | programming 测试 → 浏览器/UI 验证 |
| UI 验证用真人式操作 | programming 测试 → 浏览器/UI 验证 |
| 浏览器验证跑 WebKit | programming 测试 → 浏览器/UI 验证 |
| 焦点安全的后台浏览器 | behavior ⑦-B + programming 测试 → 浏览器/UI 验证 |

另外 **2 条环境经验**，不进 standard：

| 候选 | 落点 |
|---|---|
| Rust 编译后清理 target/ | `memory/global/exps/backend.md` 或项目级 exps |
| DSH 启动 unset ELECTRON_RUN_AS_NODE | `memory/global/exps/backend.md` 或 `user-profile` 协作环境 |

### 2.4 删除

- **操作矩阵**：按用户要求删除，不再写入任何文件。

---

## 3. behavior-standards.md 目标结构

原则不变：**硬性约束（对抗模型天性）→ 工作方式（怎么干活）→ 整体意识（怎么思考）**。

```text
硬性约束
  总纲
  ① 事实断言先查证          ← 触发项增加“数据量/规模/成本”
  ② 结论先证伪
  ③ 完成先过清单            ← 增加“同类入口全扫”
  ④ 走不通就认账换路
  ⑤ 用户观察 > 我的判断      ← 增加“不甩锅”的具体触发
  ⑥ 说完成即审查（分级）     ← 完整审查 / 轻量验证两档
  ⑦ 两道闸门
     ⑦-A 没指令不碰代码（范围闸）
     ⑦-B 不请示不做（权限闸） ← 增加破坏性操作、窗口/焦点
  ⑧ 禁止加戏
  自省闭环

工作方式
  Plan
  环境探测（新）            ← 检索工具 / FlClash / gh / 硬件
  调研 / 搜索               ← 用户文件当输入
  沟通                      ← 用户顺手 / 截图 / 开干
  交付写作（P0）            ← 28/29
  干活流程
  子代理调研
  环境故障停止

整体意识
  整体图优先
  画图时机
  看图说话
  自问清单
  资源边界                  ← 新增：无上限不注入
  对待错误
```

### 3.1 ⑦ 拆成两道闸门

```markdown
## ⑦ 两道闸门：没指令不碰代码 / 不请示不做

### ⑦-A 没指令不碰代码（范围闸）
🔴 只改用户点名的问题；不顺手修别的 bug、不重构、不格式化、不扩展。
- 看到任务之外的 bug/坏味道：先报告，等用户决定；不合并进本次改动。
- 读文件、跑测试、查日志不受此限；它限制的是“改什么代码”。

### ⑦-B 不请示不做（权限闸）
🔴 即使在做 ⑦-A 允许的事，下列副作用动作也先请示：
- git 操作（commit/push/merge/开分支/改版本号）
- 创建/删除/移动文件
- 修改配置（settings/config/环境）
- 运行改动系统状态的命令（安装/卸载/重签名/改系统文件）
- 破坏性操作（kill/删除/覆盖/迁移）：先确认目标与影响范围；只读命令不适用
- 打开/激活可见窗口、切换前台应用、模拟鼠标键盘：默认后台；要前台先请示
- 任何“你没明确说”的事
```

区别：**⑦-A 管“能改哪块代码”，⑦-B 管“就算在范围内，哪些动作也得先问”。**

### 3.2 ⑥ 改成两档审查

```markdown
## ⑥ 说完成即审查（分级）

触发：说“完成/修好了/没问题/做完了/交付/方案定了”；被用户质疑后；同一问题修 >2 次。

审查强度：
- 完整独立审查：数据/安全/并发/持久化/迁移、多文件、用户质疑、同一问题修 >2 次。
- 轻量验证：无持久化的小 UI/文案/样式；构建通过 + 用户目测即可，不派重审查。

审查任务书：写清目标、死清单、范围、输出格式；不走全量、不重复用户已做的验证。
收到结论必须修正，禁止辩护。
```

### 3.3 交付写作（P0）

```markdown
### 交付写作（P0）

- 🔴 先问读者：谁读、怎么读、看到会怎样。内部理由改写成客观约束；不把内部权谋/口径/未定策略写进交付物。
- 🔴 只写交付内容：读者需要的事实/决策/操作/验收；不写“文档目的/范围”、不写“已剔除项/内部待办”、不把工作过程/内部底稿当正文。
- 🟡 内部底稿与交付物分开存。
```

反例：❌“因为老板不想让客户知道……” → ✅“该字段对客户不可见，接口不返回。”

### 3.4 其他增量

- ① 触发项增加：**数据量与规模**（行数、文件大小、token、成本、迁移条数）。
- ③ 清单增加第 5 条：**同类入口全扫**（同类代码路径/配置入口/临界区间都枚举了吗）。
- ⑤ 增加触发：修完仍不对、用户说“还是这样” → 先查渲染/代码/数据路径；禁止归因缓存或“你没看最新”。
- 沟通增加：
  - 用户手动更便宜时直接开口；自己试两条路不通就问，不硬啃。
  - 用户说“截图了”：去 Desktop/Downloads/Pictures/Documents 找最近图片并 Read，不问路径。
  - 用户已细化一件并说“开干”：视为那批整体认可；只做那批，不扩散。
- 调研/搜索增加：拿用户真实文档/代码当输入前，先说明用哪些、怎么用；默认只读 + `/tmp`；被问给 mtime/ctime 证据。
- 新增「资源边界」：

```markdown
### 资源边界
- 🔴 任何注入/上下文/工具输出先问上限；无上限不注入。
- 段号/路径清单可以，整份文档/全量日志不行；超限先裁剪/分页/按需读取。
- 判断资源占比（token/时间/注意力/缓存），占小的别当大的吹。
```

---

## 4. programming-standards.md 目标结构

原则不变：各节平铺，按工程域组织。

```text
Git
代码
  可拓展
  可读                      ← 注释只写现状
  低耦合 高内聚
  鲁棒
  可测试
  可维护                    ← 参数必须有依据
  高效
  安全                      ← 不打印 config 原文
  明确核心模块职责边界
测试
  测试设计                  ← 真实失败路径 / 验证范围 / 基准先验
  浏览器 / UI 验证（新）
  CI / 质量门禁
  CI 设计思路
文档
端口 / 网络
构建、发布与分发
  自包含便携分发优先
  GitHub Actions 多平台构建
  预发布与正式发布流水线
  前端构建一致性（新）
  边界与约束
```

### 4.1 测试设计增量

```markdown
- 用例必须全面：正常/异常/边界/空值/并发。
- 回归测试必须复现用户的真实失败路径；自编脚本容易假绿。
- 交付前的人工/端到端验证只覆盖本次改动路径；全量/全页穷举先问用户，除非改动是全局性的。
- 以外部工具/基准做对比前，先用最小样本验证基准本身可信。
- 严禁针对测试用例走捷径。
```

### 4.2 浏览器 / UI 验证（新）

```markdown
#### 浏览器 / UI 验证

- 🔴 不得抢焦点：macOS 默认用 `open -g` 起 Chrome for Testing + `connect_over_cdp` 后台操作；禁止 `launch(headless=False)` 直接弹前台。只有纯渲染 bug 才用前台模式，且必须先跟用户打招呼。
- 🟡 每次全新 profile：不复用；收尾按临时 profile 目录名杀进程并等待退出，再删目录。
- 🟡 等待用轮询：不用固定 `sleep`；点击后用 aria/可见性/状态断言确认真的生效。
- 🟡 真人操作：真鼠标/键盘；数据抽 DOM；视觉/归属截图并自己 Read，不只看文字描述。
- 🟡 JS 页面用浏览器抓：curl 抓不到不等于做不到。
- 🟡 先 headless 做功能验证；涉及“看不见/遮挡/渲染/像素”再用真窗口后台模式。
- 🟡 Chromium + WebKit 都跑；WebKit headless 不等于真 Safari 渲染路径；真 WebKit 渲染问题需用户可见验证或提前请示。
```

### 4.3 代码增量

- 可读：注释只描述当前行为；历史/废弃路径单独标，不写过期事实，不指向不存在的符号。
- 可维护：间距/尺寸/阈值/超时等参数必须有依据（规范/公式/成熟实现/实测），不凭感觉调。
- 安全：读取配置/凭证时只取需要的字段；禁止把 config 原文整段打印/贴出；需要展示时过滤/脱敏。

### 4.4 前端构建一致性（新）

```markdown
#### 前端构建一致性

- 改前端源码后必须重新构建产物；typecheck/测试通过不代表 bundle 已更新。
- 提交/部署前确认构建时间/哈希与源码一致。
```

---

## 5. OASIS 怎么进长期记忆

### 5.1 结论

**两边都要，但代码不塞进 standard。** 采用三层渐进式披露：

| 层 | 放什么 | 放哪 | 是否每轮注入 |
|---|---|---|---|
| 规范层 | 硬规则与不变量：不抢焦点、轮询、真操作、WebKit、headless 边界 | `programming-standards.md` → 测试 → 浏览器/UI 验证 | 是，十几行 |
| 技能层 | 可执行代码：后台 `open -g` + CDP、临时 profile、端口归属校验、清理 | `memory/global/skills/browser-probe/SKILL.md` + `scripts/browser_probe.py` | 否，按需 |
| 经验层 | OASIS 踩坑：坐标被夹、profile 复用卡 180 秒、`pgrep --` 失效、后台不画像素 | `memory/global/exps/frontend.md` | 否，按需 |

### 5.2 为什么不是“代码直接包进 standard”

- standard 是每轮注入的静态段，`_browser.py` 270 行，进去就是纯 token 成本。
- 代码里有 OASIS 专用选择器（`STATUS_PARA_JS`、`SEARCH_COUNT_JS`、`select_text_in_first_paragraph`），不应污染全局。
- 标准是散文，代码会过期；代码应该可执行、可测试、按需加载。

### 5.3 为什么不是“只开一个新 standard 讲原理”

- `open -g`、端口归属校验、按 profile 杀进程这些细节很容易写错。
- 只讲原理，下个项目还得重写，极可能再次抢焦点。

### 5.4 代码提取方式

从 `OASIS/scripts/probe/_browser.py` 抽通用部分：

- 保留：`open_browser`、`_chrome_app`、`_free_port`、`_wait_cdp`、`_port_is_ours`、`_kill_by_profile`、`atexit` 清理。
- 移除：OASIS 专用 JS 选择器和 `select_text_in_first_paragraph`；这些放 `exps/frontend.md` 当案例。
- 改名：`OASIS_PROBE_MODE` → `MIND_PROBE_MODE`（或参数 `front=True`）。
- 增加：`browser="chromium" | "webkit"`。Chromium 走后台 CDP；WebKit 没有 CDP 后台方案，默认 headless，真窗口 WebKit 只能用户可见验证或提前请示。
- 标准里只留一句：`可执行实现见 skills/browser-probe/SKILL.md；踩坑见 exps/frontend.md。`

`memory/global/skills` 本来就是按需层：`scripts/skills_sync.py` 明确它是内容源，inject 用非递归 glob 天然不扫这个子目录。

---

## 6. 环境事实：检测习惯（不是断言）

> 原则：**不把当前端口、内存、工具可用性写成永久断言**。每次先检测，按结果选择路径；当前值只放带日期的观测快照。

### 6.1 拟写入 behavior-standards 的正式文本

> 只写规则。原因、历史、观测、工具差异说明放 6.2 和 `user-profile`，不进规范。

```markdown
### 环境探测（做之前，按需）

- 🟡 检索工具按运行环境选择：
  - Claude Code：先用 WebSearch；WebFetch 失败一次即改用 `curl`。
  - DSH：使用 DSH 原生 web 工具。
- 🔴 网络先走 FlClash：
  1. 使用 FlClash 代理（配置见 `user-profile`）。
  2. 代理不通 → 通知用户开 FlClash，暂停依赖网络的工作。
  3. 用户确认已开仍不通 → 与用户共同排查（端口、系统代理、TUN、DNS、证书）；解决前不继续其他工作。
  4. 禁止直连硬撑、降级跳过、转入其他任务。
- 🔴 `gh` 优先走代理：
  - 使用 `HTTPS_PROXY` / `HTTP_PROXY` 或系统代理。
  - 用 `git ls-remote` / `gh auth status` 验通路；失败按 FlClash 流程处理。
- 🟡 硬件按实际值选型：
  - 涉及选型、并发或内存预算时，先读取实际 RAM/CPU。
```

### 6.2 2026-10-20 观测快照（非规范，排查用，随时可过期）

- 硬件：MacBook Pro Mac17,9，Apple M5 Pro，15 核，24GB，macOS 26.6.1 arm64。
- 代理：系统 HTTP/HTTPS/SOCKS `127.0.0.1:7890`，FlClashCo 监听；git 全局 proxy 也是 7890；31181/31136 未监听。
- GitHub：直连 `github.com` 表现不稳定（一次超时、一次 200）；`raw` 直连 reset；经 7890 全部可达；`git ls-remote` 成功；`gh auth` 为 Alex-Fleet，本次直连成功（仅快照）。
- Claude Code WebFetch：10 个国内外域名（example.com、github.com、api.github.com、raw、npmjs、pypi、arxiv、MDN、baidu、zhihu）全部报 `Unable to verify if domain ... is safe to fetch`；WebSearch 可用。DSH 原生 fetch 正常（用户确认）。
- curl 直连/代理：大多数域名直连和 7890 均可返回 200；`raw` 直连 reset、pypi 直连超时、github 直连不稳定；7890 下均可达。npmjs 返回 403（站点侧限制，不是网络不通）。

---

## 7. 待讨论

1. 3–10 的语境与落点是否接受。
2. ⑥ 的“完整审查 / 轻量验证”分界是否合适。
3. 环境事实是否同意放 `user-profile` 的带日期快照，而 standard 只写检测习惯。
4. OASIS skill 在 DSH 侧如何加载；若 DSH 暂无 skill 加载器，是否先作为项目脚本。
5. 项目级 turns / daily / monthly 迁移时机。
6. DSH 原生 fetch 与 `gh` 代理的具体调用方式，迁移时实测后写入 `user-profile`。

---

## 8. 进度

- 已修改 `behavior-standards.md`：29 条中的行为部分（①/③/⑤/⑥/⑦、沟通、调研、交付写作、资源边界）。
- 已修改 `programming-standards.md`：29 条中的程序部分（可读、可维护、安全、测试设计、浏览器/UI、前端构建）。
- 已更新 `user-profile.md`：协作环境快照（2026-10-20）。
- 已更新 `exps/frontend.md`、`exps/backend.md`：OASIS 后台浏览器踩坑、Rust/DSH 环境经验。
- 已创建 `memory/global/skills/browser-probe/`：`SKILL.md` + `scripts/browser_probe.py`。
- 已安装到 `~/.dsh/skills/browser-probe` 和 `~/.claude/skills/browser-probe`（symlink，源在 `memory/global/skills`）。
- `browser-probe` 自测：Chromium 与 WebKit 均通过（前台 App 不变、`clicked`、无 orphan、退出码 0）。
- 2026-10-21 执行：删除/归档 9 条（OASIS「交付流程与操作矩阵」保留待议）；环境条目 7→5；敏感信息改为指针；全局经验 2 条进 `exps/cross-cutting.md`；`exps/database.md`、`exps/cross-cutting.md` 补齐；checklists 去 MIND 化、修重复标题；`math-research-standards.md` 归档并移出注入；项目级 23 条迁到 `memory/projects/<project>/rules.md`；Level 1 已复制到 `~/.dsh/mind/global/`。
- 仍未做：36 条全局规则的源 MEMORY.md 索引未删（内容已进 standards）；OASIS「交付流程与操作矩阵」待议；迁移临时条待删；DSH skill 需在新会话目测。
- 2026-10-22：38 条全局规则/经验源条目归档到 `memory/archive/migrated-memory-entries/`；`user-profile.md` 和 `exps-index.md` 加入 DSH 静态标准段；exps / checklists 正文继续按需读。`exps-index` 明确标注“经验不是硬性规范”。

---

## 9. 后续低优先级

- 提案区体验：按 workspace / 来源 session 过滤、批量拒绝、显示来源与上下文。暂不处理，先记一笔。

