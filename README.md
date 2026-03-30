# NAS Tavily Stack


这是一个适合部署到 NAS 的 Tavily 多 Key 轮询方案，包含两个服务：

- `nas-tavily-gateway`：负责多个 Tavily API Key 的轮询、失败切换，并调用 Tavily Search API
- `nas-tavily-mcp`：提供 MCP Server，对外暴露 `tavily-search` 工具，并把请求转发到 Gateway

---

## 架构

本地客户端（Cursor / Claude / 其他）
→ `nas-tavily-mcp`
→ `nas-tavily-gateway`
→ Tavily Search API

---

## 目录结构

- `gateway/`：Python FastAPI 网关
- `mcp/`：Node.js MCP Server
- `deploy/nas/`：NAS 部署文件
- `.github/workflows/`：GitHub Actions 自动构建并推送到 DockerHub

---

## 先决条件

1. GitHub 仓库
2. DockerHub 账号
3. Tavily API Keys
4. NAS 上可运行 Docker / Container Manager

---

## GitHub Secrets

在 GitHub 仓库中配置：

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

---

## 构建与发布

push 到 `main` 后，GitHub Actions 会自动：

1. 构建 gateway 镜像
2. 构建 mcp 镜像
3. 推送到 DockerHub

---


## 客户端配置 cherry studio

<img width="1174" height="791" alt="image" src="https://github.com/user-attachments/assets/74bba731-fcfb-4e4a-b924-f54532ac3c95" />
