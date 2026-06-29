# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 项目定位
- 这是一个以 `main.py` 为核心的热点聚合与关键词筛选项目。
- 主要产物：
  - 每次运行生成分时文本/HTML（`output/<日期>/txt|html`）
  - 根目录 `index.html`（当日汇总页面）
  - 静态 API 文件 `api/trends.json`
  - 报告截图 `img/news.jpg`

## 开发常用命令
### 1) 本地环境准备
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

### 2) 本地运行（核心命令）
```bash
# 常规单次执行（抓取 + 分析 + 输出 + 可选通知）
python main.py

# 仅生成静态 API/图片/汇总页面并退出
python main.py --generate-json

# 以 Flask API 服务模式运行（需安装 Flask）
python main.py --serve-api

# 清理 output 下 7 天前的目录
python clean_output.py
```

### 3) Docker 运行
```bash
# 在 docker 目录启动
cd docker
docker-compose up -d

# 容器内管理命令
docker exec -it trend-radar python manage.py status
docker exec -it trend-radar python manage.py run
docker exec -it trend-radar python manage.py logs
docker exec -it trend-radar python manage.py config
docker exec -it trend-radar python manage.py files
```

### 4) CI/自动任务相关
- `.github/workflows/crawler.yml`：安装依赖后执行 `python main.py`，并自动提交输出变更。
- `.github/workflows/cleanup.yml`：执行 `python clean_output.py`，并自动提交清理结果。

### 5) 构建/Lint/测试现状（务必注意）
- 仓库当前没有独立“构建”步骤（Python 脚本直跑）。
- 仓库当前未配置 lint 工具（如 ruff/flake8/black）。
- 仓库当前未配置测试框架与测试目录（无可直接运行的“单测命令”）。
- 需要做最小可执行验证时，使用：
```bash
python main.py --generate-json
```

## 代码架构（高层）
### 1) 配置与入口
- 配置文件：`config/config.yaml`（主配置）和 `config/frequency_words.txt`（词组规则）。
- `main.py` 在模块加载时即执行 `load_config()`，形成全局 `CONFIG`。
- 入口函数 `main()` 支持三种运行形态：
  - 默认：`NewsAnalyzer().run()`
  - `--generate-json`：只生成静态 API 与图像产物
  - `--serve-api`：启动 Flask 并暴露 `/api/trends(.json)` 与 `/img/*`

### 2) 数据采集与中间落盘
- `DataFetcher` 从 `newsnow` API 拉取各平台榜单数据。
- 每次抓取先落盘到 `output/<日期>/txt/<时分>.txt`（`save_titles_to_file`）。
- 后续统计不是只看本次抓取，而是通过 `read_all_today_titles()` 回读当天全部 txt，聚合“首次出现时间/最后出现时间/出现次数/排名轨迹”。

### 3) 词组匹配与统计核心
- `load_frequency_words()` 将词组解析为：
  - 普通词（任一命中）
  - 必须词（全部命中）
  - 过滤词（任一命中即排除）
- `count_word_frequency()` 负责：
  - 按模式（`daily/current/incremental`）选择处理数据范围
  - 识别新增标题
  - 按权重排序（排名权重 + 频次权重 + 热度权重）

### 4) 模式策略层（关键设计点）
- `NewsAnalyzer.MODE_STRATEGIES` 集中定义三种模式行为：
  - `incremental`：偏实时，仅新增触发
  - `current`：当前榜单视图 + 汇总
  - `daily`：当日汇总
- `run()` 通过策略决定：
  - 是否发送实时通知
  - 是否生成汇总页
  - 汇总按哪种模式统计

### 5) 输出与通知通道
- 报告渲染：
  - `generate_html_report()` + `render_html_content()`
  - 同步刷新根目录 `index.html`（汇总模式）
- API 产物：
  - `generate_api_data()` 组装结构化趋势数据
  - `generate_static_api_files()` 生成 `api/trends.json` 并调用 Playwright 输出 `img/news.jpg`
- 通知分发：
  - `send_to_webhooks()` 统一路由到飞书/钉钉/企业微信/Telegram
  - 支持静默推送时间窗和“每天仅推一次”（`PushRecordManager`，记录在 `output/.push_records/`）

### 6) 运行环境分支逻辑
- GitHub Actions：通过 `GITHUB_ACTIONS=true` 判断，通常不走代理，并在工作流中注入 webhook secrets。
- Docker：`docker/entrypoint.sh` + supercronic 承担定时执行；`docker/manage.py` 提供容器内运维命令。
- 本地：默认可打开浏览器查看 HTML 报告（非 Docker/非 Actions）。

## 修改时的高风险点
- `main.py` 为单文件大入口，函数间通过 `CONFIG` 与文件产物耦合紧密；改动流程时要同时核对：
  - txt 落盘格式与回读解析是否兼容
  - 三种模式策略是否保持一致
  - 通知内容分片大小与平台格式差异（尤其 Telegram/飞书）
- `config/config.yaml` 中 webhook 字段可被环境变量覆盖；排查通知问题时优先确认“最终生效来源”。
