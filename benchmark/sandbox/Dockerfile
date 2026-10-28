# 评测沙箱: node(pi runner) + python3/pytest(任务运行时)
FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install pytest
WORKDIR /benchmark
COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY runner ./runner
# 沙箱运行: 挂载任务目录 + 跑 task-runner（容器内 cwd = /benchmark）
ENTRYPOINT ["node", "runner/task-runner.mjs"]
