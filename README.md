# PyNovel-AI 🚀

> **全自动、具备长期记忆的 AI 小说生成引擎**
> *Auto-generate novels with Long-term Memory & State Tracking*

PyNovel-AI 是一个轻量级但强大的 AI 小说创作系统。它不仅仅是调用 LLM 写作，更内置了 **RAG 向量记忆** 和 **世界状态追踪**，确保长篇连载逻辑连贯，伏笔必收。

## ✨ 核心特性

*   **🧠 长期记忆 (RAG)**：内置轻量级向量数据库，自动记忆百章前的伏笔与设定，告别“AI 健忘症”。
*   **🌍 动态世界状态**：实时追踪角色状态（HP、位置、物品）与剧情线（未填的坑），自动更新并注入写作上下文。
*   **⚙️ 全自动闭环**：`auto_runner` 支持从创意 → 配置 → 大纲 → 正文 → 反思复盘的无人值守循环。
*   **🔌 多模型支持**：原生支持 **Google Gemini** (推荐) 与 **OpenAI** 协议模型。
*   **🛡️ 鲁棒性设计**：包含敏感内容自动修正、逻辑一致性自检及断点续传功能。

## � 项目结构

```text
PyNovel-AI/
├── auto_runner.py        # 🚀 [入口] 一键启动自动化循环
├── configs/              # ⚙️ 配置文件仓库
├── core/
│   ├── generator.py      # 核心写作逻辑
│   ├── state_manager.py  # 状态与记忆管理器
│   └── rag_engine.py     # 轻量级向量检索引擎
├── drivers/              # LLM 驱动 (Gemini, OpenAI)
├── novels/               # 📖 生成的小说 (含记忆库 memory.json)
├── tools/                # 辅助工具 (创意生成、配置生成)
└── .env                  # API 密钥配置
```

## ⚡️ 快速启动

1.  **环境准备**
    ```bash
    git clone https://github.com/YourName/PyNovel-AI.git
    cd PyNovel-AI
    pip install -r requirements.txt
    ```

2.  **配置密钥**
    复制 `.env.example` 为 `.env` 并填入密钥：
    ```ini
    LLM_PROVIDER=gemini  # 或 openai
    LLM_API_KEY=your_api_key_here
    ```

3.  **运行**
    *   **全自动模式**（推荐）：
        ```bash
        python auto_runner.py
        # 修改 auto_runner.py 中的 FIXED_IDEA 变量可指定题材
        ```
    *   **手动模式**：
        ```bash
        python main.py
        ```

## 🛠️ 进阶配置

在 `configs/` 下可创建通过 YAML 定义的精细化小说配置，或通过 `auto_runner` 自动生成。

```yaml
# 示例配置片段
title: "我的修仙传"
genre: "玄幻"
model_name: "gemini-2.0-flash-exp"
world_view: "末法时代，灵气复苏..."
```

---
*Powered by Python & LLMs.*
