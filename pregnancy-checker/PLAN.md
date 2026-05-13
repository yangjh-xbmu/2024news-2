# 孕期食品配料表检查工具 — 实施计划

## 架构总览

```
浏览器(index.html) → Flask(server.py) → MinerU Precision API(OCR)
                                       → DeepSeek V4 Pro(成分分析)
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `pregnancy-checker/server.py` | Flask 后端，处理上传 + 调用两个 API |
| `pregnancy-checker/index.html` | 前端单页，上传 + 进度 + 结果展示 |
| `pregnancy-checker/requirements.txt` | Python 依赖 |
| 项目根 `.env` | `mineru-ak` + `ds-api-key` |

---

## 任务拆解

### 任务 1：编写 `requirements.txt`

**操作**：创建文件，写入依赖清单。

**内容**：
```
flask
requests
python-dotenv
```

**验证**：`pip install -r requirements.txt` 无报错。

---

### 任务 2：创建 `server.py` — Flask 骨架 + 根路由

**操作**：创建 Flask app，加载 `.env`，添加 `/` 路由返回 `index.html`，添加 `/api/analyze` 空端点。

**文件**：`pregnancy-checker/server.py`

**伪代码**：
```
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

load_dotenv('../.env')
app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    # TODO: 后续任务填充
    pass
```

**注意**：`static_folder` 设为当前目录 `'.'`，使 Flask 能 serving 同目录下的 `index.html`。

**验证**：启动后 `curl http://localhost:5000/` 返回 HTML（目前可能 404，因为 index.html 还没创建）。

---

### 任务 3：MinerU OCR 函数 — 获取上传 URL + 上传文件

**操作**：在 `server.py` 中新增 `ocr_extract(image_bytes, filename)` 函数。

**流程**：
1. POST `https://mineru.net/api/v4/file-urls/batch`，body 为 `{"files": [{"name": filename}], "model_version": "vlm"}`，Header 带 `Authorization: Bearer {MINERU_TOKEN}`
2. 从响应取 `batch_id` 和 `file_urls[0]`
3. PUT `image_bytes` 到 `file_urls[0]`（不带 Content-Type header）
4. 返回 `batch_id`

**验证**：函数返回有效的 `batch_id`（UUID 格式字符串）。

---

### 任务 4：MinerU OCR 函数 — 轮询结果 + 下载 Markdown

**操作**：在 `server.py` 中新增 `ocr_poll(batch_id)` 函数。

**流程**：
1. GET `https://mineru.net/api/v4/extract-results/batch/{batch_id}`，带 Auth header
2. 检查 `extract_result[0].state`：
   - `done` → 取 `full_zip_url`，下载 ZIP，解压取 `full.md` 内容，返回文本
   - `running` / `pending` → sleep 3s，重试
   - `failed` → 抛出异常，返回 `err_msg`
3. 超时上限 120s

**验证**：用已知图片测试，返回可读的 Markdown 文本。

---

### 任务 5：DeepSeek 分析函数

**操作**：在 `server.py` 中新增 `analyze_ingredients(ocr_text)` 函数。

**流程**：
1. POST `https://api.deepseek.com/chat/completions`，Header `Authorization: Bearer {DS_API_KEY}`
2. Body 包含 system prompt（孕妇食品安全知识库）+ user message（OCR 提取的配料文本）
3. 请求结构化 JSON 输出
4. 解析响应，返回 dict

**System Prompt 核心内容**（编译自 ACOG、FDA、WHO、中国居民膳食指南）：

```
你是孕期食品安全分析专家。根据以下权威来源的规则，分析食品配料表：

## 禁用（Avoid）
- 酒精及含酒精成分
- 未经巴氏消毒的乳制品（生奶、软质奶酪如布里、卡门贝尔、蓝纹奶酪等）
- 生或未煮熟的海鲜、肉类、禽肉、蛋类
- 高汞鱼类：鲨鱼、剑鱼、国王鲭鱼、方头鱼、大眼金枪鱼
- 冷藏即食熟食肉（冷切肉、火腿、萨拉米等，除非彻底加热至冒热气）
- 冷藏烟熏海鲜（除非彻底加热）
- 生芽菜（苜蓿芽、豆芽、萝卜芽等）
- 未经巴氏消毒的果汁/苹果酒

## 慎用/限量（Caution）
- 咖啡因：每日不超过200mg（约1-2杯咖啡）；配料表中咖啡、浓茶、可乐、能量饮料成分需提示
- 动物肝脏及肝脏制品：维生素A过量有致畸风险
- 中药材成分需特别标注并建议咨询医生：薏苡仁/薏米、山楂、马齿苋、芦荟（内服）、藏红花（大剂量）、川芎、当归
- 人工甜味剂：糖精（可穿过胎盘）、甜蜜素建议避免；阿斯巴甜（苯丙酮尿症患者除外）一般安全
- 硝酸盐/亚硝酸盐（防腐剂 E249-E252）：提示加工肉制品风险
- 高盐食品：提示妊娠期高血压风险

## 安全（Safe）
- 巴氏消毒乳制品
- 彻底煮熟的肉类、禽肉、蛋类
- 低汞鱼类（三文鱼、沙丁鱼、鳟鱼、鳕鱼、鲶鱼）
- 洗净的新鲜蔬菜水果
- 全谷物
- 叶酸、铁、钙天然来源的食物

## 输出格式
严格输出以下 JSON，不要包含任何其他文字：

{
  "overall_verdict": "safe" | "caution" | "avoid",
  "summary": "一句话总结",
  "ingredients": [
    {
      "name": "配料名",
      "risk": "safe" | "caution" | "avoid",
      "reason": "判定依据，引用具体权威来源",
      "evidence_level": "strong" | "moderate" | "traditional"
    }
  ]
}
```

**User Message**：
```
请分析以下食品配料表，逐项判定是否适合孕妇食用：

{ocr_text}
```

**验证**：手动传入一段配料文本（如"配料：小麦粉、白砂糖、食用酒精、碳酸氢铵"），返回合法 JSON，酒精标记为 `avoid`。

---

### 任务 6：连接 `/api/analyze` 端点

**操作**：填充任务 2 中的 `analyze()` 函数。

**流程**：
1. 从 `request.files['image']` 取文件，读字节和文件名
2. 调用 `ocr_extract()` → `ocr_poll()` 获取 OCR 文本
3. 调用 `analyze_ingredients(ocr_text)` 获取分析结果
4. 返回 `jsonify(analysis_result)`

**错误处理**：
- 无文件上传 → 400
- MinerU 失败 → 502，附带 `err_msg`
- DeepSeek 失败 → 502，附带错误信息
- DeepSeek 返回非 JSON → 尝试修复解析，失败则 502

**验证**：上传一张配料表图片，curl `/api/analyze` 返回完整 JSON。

---

### 任务 7：编写 `index.html` — 上传界面 + 进度条

**操作**：创建单页 HTML，包含：
- 标题："孕期食品配料表检查"
- 上传区域（拖拽 + 点击），支持 JPG/PNG
- 图片预览
- 三个阶段的进度指示器：提取文字 → 分析配料 → 完成
- 结果展示区域（初始隐藏）

**样式要求**：
- 移动端优先（max-width 640px 居中），PC 也兼容
- 简洁专业，适合课堂投影（字体够大）
- 上传区域虚线边框，hover 高亮

**验证**：浏览器打开 `http://localhost:5000/`，拖拽图片能看到预览。

---

### 任务 8：编写 `index.html` — 结果展示 + JS 交互

**操作**：添加 JavaScript 逻辑：
1. 上传/选择图片后显示预览
2. 点击"开始分析" → POST `/api/analyze`（FormData）
3. 轮询或等待响应期间更新进度条
4. 收到结果后渲染：
   - 顶部：总体判定（绿色 Safe / 黄色 Caution / 红色 Avoid 大标签）
   - 一句总结
   - 逐项配料卡片：名称 + 风险标签色 + 理由 + 证据等级
   - 底部：免责声明

**验证**：全流程测试，上传图片 → 看到结果。

---

### 任务 9：启动脚本 + 最终验证

**操作**：
1. 确认 `python server.py` 在 `pregnancy-checker/` 目录下可启动
2. 添加 Flask 启动入口 `if __name__ == '__main__': app.run(debug=True, port=5000)`
3. 端到端测试：准备一张配料表图片，启动服务，浏览器打开，上传，看到完整分析结果

**验证**：整个流程无报错，结果展示完整。

---

## 执行顺序

```
任务1 → 任务2 → 任务3 → 任务4 → 任务5 → 任务6 → 任务7 → 任务8 → 任务9
```

依赖关系是线性的，每个任务依赖前一个完成。任务 7 和任务 8 可以与任务 3-6 并行开发（但通常在逻辑上排在后端完成后更易验证）。
