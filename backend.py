# -*- coding: utf-8 -*-
"""
小说分析器后端
基于FastAPI的轻量级Web服务
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI(
    title="小说分析器",
    description="基于LLM的小说分析工具 - 多角色、多关系、性癖分析",
    version="2.0.0"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

NOVEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_NOVEL_PATH = NOVEL_ROOT


class AnalyzeRequest(BaseModel):
    content: str
    api_url: str
    api_key: str
    model: str


def extract_json_from_response(text: str) -> Dict[str, Any]:
    """从LLM响应中提取JSON"""
    if not text or len(text.strip()) < 5:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, TypeError):
        pass

    return {}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/novels")
def scan_novels():
    """递归扫描所有.txt小说文件"""
    base_path = DEFAULT_NOVEL_PATH

    exclude_keywords = {'venv', '__pycache__', '.git', 'node_modules', 'pip', 'site-packages', 'dist-info', '.tox', '.eggs', 'novel-analyzer'}

    novels = []

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in exclude_keywords and not d.startswith('.')]

        folder_name = os.path.basename(root)

        if root == base_path:
            continue

        root_lower = root.lower()
        if any(keyword in root_lower for keyword in exclude_keywords):
            continue

        txt_files = []
        for f in files:
            if f.endswith('.txt') and not f.startswith('.'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, base_path)
                txt_files.append({
                    "name": f,
                    "path": rel_path,
                    "size": os.path.getsize(full_path)
                })

        if txt_files:
            novels.append({
                "folder": folder_name,
                "path": folder_name,
                "files": sorted(txt_files, key=lambda x: x['name'])
            })

    return {"novels": novels, "total": sum(len(n['files']) for n in novels)}


@app.get("/api/novel/{path:path}")
def read_novel(path: str):
    """读取指定小说内容（限制长度）"""
    base_path = DEFAULT_NOVEL_PATH
    full_path = os.path.join(base_path, path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    if not full_path.endswith('.txt'):
        raise HTTPException(status_code=400, detail="仅支持.txt文件")

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if len(content) > 80000:
            content = content[:80000] + "\n\n... (内容已截断，分析可能不完整)"

        return {
            "name": os.path.basename(path),
            "path": path,
            "content": content,
            "length": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取失败: {str(e)}")


@app.post("/api/test-connection")
def test_connection(req: AnalyzeRequest):
    """测试API连接"""
    if not req.api_url or not req.api_key or not req.model:
        raise HTTPException(status_code=400, detail="请填写完整的API配置")

    try:
        response = requests.post(
            f"{req.api_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {req.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": req.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            },
            timeout=30
        )

        if response.status_code == 200:
            return {"status": "success", "message": "连接成功"}
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', response.text)
            except:
                error_msg = response.text
            raise HTTPException(status_code=response.status_code, detail=f"API错误: {error_msg}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="请求超时")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@app.post("/api/analyze")
def analyze_novel(req: AnalyzeRequest):
    """调用LLM分析小说 - 支持多角色多关系"""
    if not req.api_url or not req.api_key or not req.model:
        raise HTTPException(status_code=400, detail="请填写完整的API配置")

    prompt_v1 = f"""
As a professional literary analyst specializing in adult fiction, analyze this novel comprehensively.

## Analysis Requirements

### 0. NOVEL METADATA
Extract basic novel information:
- World setting/background (genre, time period, universe type)
- Estimated chapter count (count chapter markers like "第X章", "Chapter X", etc.)
- Completion status (based on ending - does story conclude or feel unfinished?)

### 1. SEXUAL CHARACTERS ONLY
Identify ONLY characters who engage in sexual activities (只包含有性行为的角色):
- Name/alias
- Gender role: male/female
- Identity: occupation, age, social status
- Personality traits
- SEXUAL PREFERENCES & KINKS: Describe what this character enjoys in bed:
  - Position preferences
  - Role in sex (dominant/submissive/equal)
  - Specific kinks: anal, oral, vaginal, BDSM, foot fetish, cum, creampie, gangbang, etc.
  - Any fetishes mentioned: foot worship, body worship, anal play, etc.
  - Personality in bed: aggressive, shy, experienced, virgin, etc.
- FOR FEMALE CHARACTERS ONLY - 淫荡指数 (Lewdness Index) - REQUIRED FOR ALL FEMALES:
  - Score 1-100 based on: sexual frequency, initiative, variety of partners, openness to kinks
  - EVERY female character MUST have lewdness_score and lewdness_analysis
  - Provide brief analysis explaining the score

### 2. ALL SEXUAL RELATIONSHIPS
Map every sexual relationship in the novel:
- Who with whom
- Relationship type: one-night stand/regular/FWB/lover/spouse/etc.
- How it started

### 3. FIRST SEX SCENES FOR EACH PAIR
For each sexual pair, find their first intimate scene:
- Characters involved
- Chapter location
- Scene description (under 50 chars)

### 4. COMPLETE INTIMACY STATISTICS
For ALL sexual activities in the novel:
- Total scene count
- For each scene: chapter, participants, location, description

### 5. SEXUAL EVOLUTION
Track how sexual relationships develop:
- Key milestones for each pair

### 6. DETAILED SUMMARY
Write a comprehensive summary (200-300 characters) covering:
- Main plot and story arc
- Core sexual themes and dynamics
- Key character relationships

## Output Format (JSON ONLY)

```json
{{
    "novel_info": {{
        "world_setting": "世界观设定描述（类型、背景、时代）",
        "chapter_count": 章节数,
        "is_completed": true/false,
        "completion_note": "完结状态说明"
    }},
    "characters": [
        {{
            "name": "角色名",
            "gender": "male/female",
            "identity": "身份描述",
            "personality": "性格特点",
            "sexual_preferences": "详细的性癖爱好描述",
            "lewdness_score": 85,
            "lewdness_analysis": "淫荡指数分析说明(仅女性角色填写)"
        }}
    ],
    "relationships": [
        {{
            "from": "角色A",
            "to": "角色B",
            "type": "一夜情/固定炮友/恋人/夫妻/暗昧",
            "start_way": "如何开始",
            "description": "关系描述"
        }}
    ],
    "first_sex_scenes": [
        {{
            "participants": ["角色A", "角色B"],
            "chapter": "第X章",
            "location": "地点",
            "description": "描述"
        }}
    ],
    "sex_scenes": {{
        "total_count": 总次数,
        "scenes": [
            {{"chapter": "章节", "participants": ["参与者"], "location": "地点", "description": "描述"}}
        ]
    }},
    "evolution": [
        {{"chapter": "章节", "stage": "阶段", "description": "描述"}}
    ],
    "summary": "详细总结(200-300字)"
}}
```

## Notes
- ONLY include characters who have sexual activities (not all characters)
- Be thorough about sexual preferences
- Output MUST be valid JSON only

## Novel Content

{req.content}
"""

    prompts = [
        ("multi-character", prompt_v1)
    ]

    analysis = None
    last_error = None
    raw_response = None
    _last_api_response = [None]  # Mutable container for nested function access

    def call_llm_with_response(prompt, retry_count=3):
        """调用LLM API，带重试机制，同时保存原始响应"""
        last_error = None

        for attempt in range(retry_count):
            _last_api_response[0] = None
            try:
                response = requests.post(
                    f"{req.api_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {req.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": req.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 1.0
                    },
                    timeout=180
                )

                _last_api_response[0] = response.text[:3000]  # 保存原始响应到外部可访问的容器

                if response.status_code in [502, 504, 503]:
                    import time
                    wait_time = 5 * (attempt + 1)
                    last_error = f"网关超时({response.status_code})"
                    time.sleep(wait_time)
                    continue

                if response.status_code == 429:
                    import time
                    wait_time = 5 * (attempt + 1)
                    last_error = f"请求频繁(429)"
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    error_msg = f"API错误: {response.status_code}"
                    if response.status_code == 401:
                        error_msg = "API密钥无效"
                    elif response.status_code == 403:
                        error_msg = "无权限访问"
                    elif response.status_code == 400:
                        error_msg = "请求参数错误"
                    elif response.status_code == 421:
                        error_msg = "内容审核拦截(421)"
                    raise Exception(error_msg)

                result = response.json()
                message = result['choices'][0]['message']
                content = message.get('content', '') or message.get('reasoning_content', '') or ''

                if not content or len(content.strip()) < 10:
                    raise Exception(f"返回内容过短")

                return content

            except requests.exceptions.Timeout:
                last_error = f"超时({attempt + 1}/3)"
                if attempt < retry_count - 1:
                    import time
                    time.sleep(3)
                    continue
                raise Exception(last_error)
            except Exception as e:
                if attempt < retry_count - 1 and any(x in str(e) for x in ['502', '504', '503', '429', 'timeout', 'Timeout']):
                    import time
                    time.sleep(5)
                    continue
                raise

        raise Exception(last_error)

    for style_name, prompt in prompts:
        try:
            content = call_llm_with_response(prompt)
            analysis = extract_json_from_response(content)

            if analysis and ('characters' in analysis or 'sex_scenes' in analysis):
                break
            else:
                last_error = f"数据格式异常(内容长:{len(content)})"
                raw_response = content[:1000]
        except Exception as e:
            last_error = str(e)
            # 从共享容器获取原始响应
            if _last_api_response[0]:
                raw_response = _last_api_response[0]
            continue

    if not analysis:
        error_msg = f"分析失败: {last_error}"
        if raw_response:
            error_msg += f"\n\n原始响应:\n{raw_response[:2000]}"
        elif "返回内容过短" in last_error:
            error_msg += "\n\n原始响应内容太短，API可能拦截了请求"

        raise HTTPException(status_code=422, detail=error_msg)

    return {"analysis": analysis}


if __name__ == "__main__":
    import uvicorn
    print("\n  ➜  Local:   http://localhost:6021\n")
    uvicorn.run(app, host="0.0.0.0", port=6021, log_level="warning")
