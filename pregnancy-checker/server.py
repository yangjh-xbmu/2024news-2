import io
import json
import os
import re
import time
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

MINERU_TOKEN = os.getenv("mineru-ak")
DS_API_KEY = os.getenv("ds-api-key")
MINERU_BASE = "https://mineru.net/api/v4"
DS_BASE = "https://api.deepseek.com"

app = Flask(__name__, static_folder=".")


def ocr_extract(image_bytes, filename):
    resp = requests.post(
        f"{MINERU_BASE}/file-urls/batch",
        headers={
            "Authorization": f"Bearer {MINERU_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"files": [{"name": filename}], "model_version": "vlm"},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 0:
        raise RuntimeError(f"MinerU 获取上传 URL 失败: {body.get('msg')}")

    batch_id = body["data"]["batch_id"]
    file_url = body["data"]["file_urls"][0]

    put_resp = requests.put(file_url, data=image_bytes, timeout=60)
    put_resp.raise_for_status()

    return batch_id


def ocr_poll(batch_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{MINERU_BASE}/extract-results/batch/{batch_id}",
            headers={"Authorization": f"Bearer {MINERU_TOKEN}"},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()

        if body.get("code") != 0:
            raise RuntimeError(f"MinerU 查询结果失败: {body.get('msg')}")

        result = body["data"]["extract_result"][0]
        state = result["state"]

        if state == "done":
            zip_url = result["full_zip_url"]
            zip_resp = requests.get(zip_url, timeout=60)
            zip_resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
                return zf.read("full.md").decode("utf-8")

        if state == "failed":
            raise RuntimeError(f"MinerU 解析失败: {result.get('err_msg', '未知错误')}")

        time.sleep(3)

    raise TimeoutError("MinerU 解析超时")


SYSTEM_PROMPT = """你是孕期食品安全分析专家。根据以下权威来源的规则，分析食品配料表，逐项判定是否适合孕妇食用。

## 禁用（Avoid）
- 酒精及含酒精成分。来源：ACOG, FDA, WHO
- 未经巴氏消毒的乳制品（生奶、软质奶酪如布里、卡门贝尔、蓝纹奶酪等）。来源：FDA, ACOG
- 生或未煮熟的海鲜、肉类、禽肉、蛋类。来源：FDA, ACOG
- 高汞鱼类：鲨鱼、剑鱼、国王鲭鱼、方头鱼、大眼金枪鱼。来源：FDA
- 冷藏即食熟食肉（冷切肉、火腿、萨拉米等，除非彻底加热至冒热气）。来源：CDC, ACOG
- 冷藏烟熏海鲜（除非彻底加热至冒热气）。来源：FDA
- 生芽菜（苜蓿芽、豆芽、萝卜芽等）。来源：FDA
- 未经巴氏消毒的果汁/苹果酒。来源：FDA

## 慎用/限量（Caution）
- 咖啡因：每日不超过200mg。配料表中咖啡、浓茶、可乐、能量饮料成分需提示限量。来源：ACOG
- 动物肝脏及肝脏制品：维生素A过量有致畸风险。来源：WHO, ACOG
- 中药材成分需特别标注并建议咨询医生：薏苡仁/薏米、山楂、马齿苋、芦荟（内服）、藏红花（大剂量）、川芎、当归。来源：中国药典、中医妇科临床指南
- 人工甜味剂：糖精（可穿过胎盘）、甜蜜素建议避免；阿斯巴甜一般安全但苯丙酮尿症患者除外。来源：FDA
- 硝酸盐/亚硝酸盐（防腐剂 E249-E252、亚硝酸钠、亚硝酸钾等）：提示加工肉制品风险。来源：WHO IARC
- 高盐食品：提示妊娠期高血压风险。来源：中国居民膳食指南
- 反式脂肪酸：配料表中氢化植物油、起酥油、人造黄油等需提示。来源：WHO

## 安全（Safe）
- 巴氏消毒乳制品
- 彻底煮熟的肉类、禽肉、蛋类、海鲜
- 低汞鱼类（三文鱼、沙丁鱼、鳟鱼、鳕鱼、鲶鱼等）
- 洗净的新鲜蔬菜水果
- 全谷物
- 常见食品添加剂（如碳酸氢钠/小苏打、柠檬酸、维生素C等）在正常使用量下是安全的

## 判定原则
1. 逐一分析配料表中每一项成分
2. 配料表通常按含量从高到低排列
3. 如果配料包含禁用成分，总体判定为 avoid
4. 如果没有禁用成分但有慎用成分，总体判定为 caution
5. 全部安全则判定为 safe
6. 每项判定必须引用具体权威来源
7. evidence_level: "strong" 表示 FDA/WHO/ACOG 等国际权威机构共识，"moderate" 表示有研究支持但非国际共识，"traditional" 表示中医药传统禁忌

## 输出格式
严格输出以下 JSON，不要包含任何其他文字，不要包含 markdown 代码块标记：

{
  "overall_verdict": "safe",
  "summary": "该食品所有配料均适合孕妇食用。",
  "ingredients": [
    {
      "name": "配料名",
      "risk": "safe",
      "reason": "判定依据，引用具体权威来源",
      "evidence_level": "strong"
    }
  ]
}
"""


def analyze_ingredients(ocr_text):
    resp = requests.post(
        f"{DS_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {DS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"请分析以下食品配料表，逐项判定是否适合孕妇食用：\n\n{ocr_text}",
                },
            ],
            "temperature": 0.1,
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    content = body["choices"][0]["message"]["content"]

    # 尝试提取 JSON（模型可能包裹在 markdown 代码块中）
    content = content.strip()
    m = re.search(r"\{[\s\S]*\}", content)
    if m:
        return json.loads(m.group(0))
    raise RuntimeError(f"DeepSeek 未返回有效 JSON: {content[:200]}")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "请上传图片"}), 400

    image_bytes = file.read()
    filename = file.filename or "photo.jpg"

    try:
        batch_id = ocr_extract(image_bytes, filename)
        md_text = ocr_poll(batch_id)
        result = analyze_ingredients(md_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
