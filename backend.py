# -*- coding: utf-8 -*-
"""
小说分析器后端
基于FastAPI的轻量级Web服务
"""

import os
import json
import re
import copy
import time
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import requests

load_dotenv()

DEBUG = os.getenv("DEBUG", "").strip().lower() in {"1", "true", "yes", "y"}

app = FastAPI(
    title="小说分析器",
    description="基于LLM的小说分析工具 - 多角色、多关系、性癖分析",
    version="2.0.0"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_NOVEL_PATH = Path(os.getenv("NOVEL_PATH", str(BASE_DIR.parent))).resolve()


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str


def _get_llm_config() -> tuple[str, str, str]:
    api_url = os.getenv("API_BASE_URL", "").strip()
    api_key = os.getenv("API_KEY", "").strip()
    model = os.getenv("MODEL_NAME", "").strip()
    if not api_url or not api_key or not model:
        raise HTTPException(status_code=400, detail="服务端未配置API（请在.env中设置API_BASE_URL/API_KEY/MODEL_NAME）")
    return _validate_api_url(api_url), api_key, model


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


class LLMCallError(Exception):
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


def call_llm_with_response(
    api_url: str,
    api_key: str,
    model: str,
    prompt: str,
    retry_count: int = 3,
    *,
    timeout: int = 180,
    temperature: float = 1.0,
) -> tuple[str, str]:
    last_error = None
    last_raw_response = ""

    for attempt in range(retry_count):
        try:
            response = requests.post(
                f"{api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "stream": True,
                },
                timeout=timeout,
                stream=True,
            )

            if response.status_code != 200:
                last_raw_response = (response.text or "")[:3000]
                if response.status_code in [502, 503, 504]:
                    wait_time = 5 * (attempt + 1)
                    last_error = f"网关超时({response.status_code})"
                    time.sleep(wait_time)
                    continue

                if response.status_code == 429:
                    wait_time = 5 * (attempt + 1)
                    last_error = "请求频繁(429)"
                    time.sleep(wait_time)
                    continue

                error_msg = f"API错误: {response.status_code}"
                if response.status_code == 401:
                    error_msg = "API密钥无效"
                elif response.status_code == 403:
                    error_msg = "无权限访问"
                elif response.status_code == 400:
                    error_msg = "请求参数错误"
                elif response.status_code == 421:
                    error_msg = "内容审核拦截(421)"
                raise LLMCallError(error_msg, last_raw_response)

            content = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line_text = line.decode("utf-8").strip()
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data_json = json.loads(data_str)
                        delta = data_json.get("choices", [{}])[0].get("delta", {})
                        chunk = delta.get("content", "") or delta.get("reasoning_content", "") or ""
                        content += chunk
                    except json.JSONDecodeError:
                        continue

            last_raw_response = content[:3000]

            if not content or len(content.strip()) < 10:
                raise LLMCallError("返回内容过短", last_raw_response)

            return content, last_raw_response

        except requests.exceptions.Timeout:
            last_error = f"超时({attempt + 1}/{retry_count})"
            if attempt < retry_count - 1:
                time.sleep(3)
                continue
            raise LLMCallError(last_error, last_raw_response)
        except LLMCallError:
            raise
        except Exception as e:
            raise LLMCallError(str(e), last_raw_response)

    raise LLMCallError(last_error or "调用失败", last_raw_response)


def _ensure_analysis_defaults(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantee required keys exist with sensible empty defaults to keep UI stable."""
    if not isinstance(analysis, dict):
        analysis = {}

    analysis.setdefault("novel_info", {})
    if not isinstance(analysis["novel_info"], dict):
        analysis["novel_info"] = {}
    analysis["novel_info"].setdefault("world_tags", [])
    if not isinstance(analysis["novel_info"]["world_tags"], list):
        analysis["novel_info"]["world_tags"] = []

    analysis.setdefault("characters", [])
    if not isinstance(analysis["characters"], list):
        analysis["characters"] = []

    analysis.setdefault("relationships", [])
    if not isinstance(analysis["relationships"], list):
        analysis["relationships"] = []

    analysis.setdefault("first_sex_scenes", [])
    if not isinstance(analysis["first_sex_scenes"], list):
        analysis["first_sex_scenes"] = []

    sex_scenes = analysis.get("sex_scenes")
    if not isinstance(sex_scenes, dict):
        sex_scenes = {}
    sex_scenes.setdefault("total_count", 0)
    sex_scenes.setdefault("scenes", [])
    if not isinstance(sex_scenes["scenes"], list):
        sex_scenes["scenes"] = []
    analysis["sex_scenes"] = sex_scenes

    analysis.setdefault("evolution", [])
    if not isinstance(analysis["evolution"], list):
        analysis["evolution"] = []

    analysis.setdefault("thunderzones", [])
    if not isinstance(analysis["thunderzones"], list):
        analysis["thunderzones"] = []

    analysis.setdefault("thunderzone_summary", "")
    analysis.setdefault("summary", analysis.get("summary") or "")

    return analysis

def _validate_and_fix_analysis(analysis: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    """
    Light schema validation/repair to keep frontend parsable.
    Returns (cleaned_analysis, errors).
    """
    errors: list[str] = []
    data = _ensure_analysis_defaults(copy.deepcopy(analysis or {}))

    # characters
    chars_in = data.get("characters")
    fixed_chars = []
    if isinstance(chars_in, list):
        for idx, c in enumerate(chars_in):
            if not isinstance(c, dict):
                errors.append(f"characters[{idx}] not object -> dropped")
                continue
            name = str(c.get("name") or "").strip()
            if not name:
                errors.append(f"characters[{idx}] missing name -> dropped")
                continue
            gender = str(c.get("gender") or "").strip() or "unknown"
            c["gender"] = gender
            fixed_chars.append(c)
    else:
        errors.append("characters not list -> reset")
    data["characters"] = fixed_chars

    # relationships
    rels_in = data.get("relationships")
    fixed_rels = []
    if isinstance(rels_in, list):
        for idx, r in enumerate(rels_in):
            if not isinstance(r, dict):
                errors.append(f"relationships[{idx}] not object -> dropped")
                continue
            frm = str(r.get("from") or "").strip()
            to = str(r.get("to") or "").strip()
            if not frm or not to:
                errors.append(f"relationships[{idx}] missing from/to -> dropped")
                continue
            fixed_rels.append(r)
    else:
        errors.append("relationships not list -> reset")
    data["relationships"] = fixed_rels

    # first_sex_scenes
    fss_in = data.get("first_sex_scenes")
    fixed_fss = []
    if isinstance(fss_in, list):
        for idx, s in enumerate(fss_in):
            if not isinstance(s, dict):
                errors.append(f"first_sex_scenes[{idx}] not object -> dropped")
                continue
            participants = s.get("participants")
            if not isinstance(participants, list) or not participants:
                errors.append(f"first_sex_scenes[{idx}] missing participants -> dropped")
                continue
            s["participants"] = [str(p).strip() for p in participants if str(p).strip()]
            fixed_fss.append(s)
    else:
        errors.append("first_sex_scenes not list -> reset")
    data["first_sex_scenes"] = fixed_fss

    # sex_scenes
    sex = data.get("sex_scenes") or {}
    if not isinstance(sex, dict):
        sex = {}
        errors.append("sex_scenes not object -> reset")
    scenes_in = sex.get("scenes")
    fixed_scenes = []
    if isinstance(scenes_in, list):
        for idx, s in enumerate(scenes_in):
            if not isinstance(s, dict):
                errors.append(f"sex_scenes.scenes[{idx}] not object -> dropped")
                continue
            participants = s.get("participants")
            if not isinstance(participants, list) or not participants:
                errors.append(f"sex_scenes.scenes[{idx}] missing participants -> dropped")
                continue
            s["participants"] = [str(p).strip() for p in participants if str(p).strip()]
            fixed_scenes.append(s)
    else:
        errors.append("sex_scenes.scenes not list -> reset")
    sex["scenes"] = fixed_scenes
    try:
        sex["total_count"] = max(int(sex.get("total_count") or 0), len(fixed_scenes))
    except Exception:
        sex["total_count"] = len(fixed_scenes)
        errors.append("sex_scenes.total_count invalid -> recalculated")
    data["sex_scenes"] = sex

    # evolution
    evo_in = data.get("evolution")
    if not isinstance(evo_in, list):
        data["evolution"] = []
        errors.append("evolution not list -> reset")

    # thunderzones
    th_in = data.get("thunderzones")
    fixed_th = []
    if isinstance(th_in, list):
        for idx, t in enumerate(th_in):
            if not isinstance(t, dict):
                errors.append(f"thunderzones[{idx}] not object -> dropped")
                continue
            if not t.get("type") and not t.get("description"):
                errors.append(f"thunderzones[{idx}] missing type/description -> dropped")
                continue
            fixed_th.append(t)
    else:
        errors.append("thunderzones not list -> reset")
    data["thunderzones"] = fixed_th

    # summary / thunderzone_summary
    for key in ("summary", "thunderzone_summary"):
        val = data.get(key)
        if not isinstance(val, str):
            data[key] = "" if val is None else str(val)
            errors.append(f"{key} not string -> coerced")

    # novel_info
    if not isinstance(data.get("novel_info"), dict):
        data["novel_info"] = {}
        errors.append("novel_info not object -> reset")
    else:
        novel_info = data["novel_info"]
        if not isinstance(novel_info.get("world_tags"), list):
            novel_info["world_tags"] = []
            errors.append("novel_info.world_tags not list -> reset")

    return data, errors


def _reconcile_entities(analysis: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    """
    Cross-check participants vs characters/relationships; auto-add missing pieces.
    Returns (analysis, errors)
    """
    errors: list[str] = []
    data = copy.deepcopy(analysis or {})

    characters = data.get("characters") or []
    relationships = data.get("relationships") or []
    first_scenes = data.get("first_sex_scenes") or []
    sex = data.get("sex_scenes") or {}
    sex_scenes = sex.get("scenes") or []

    name_set = {c.get("name") for c in characters if isinstance(c, dict) and c.get("name")}

    def _collect_participants():
        parts = set()
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            frm = str(rel.get("from") or "").strip()
            to = str(rel.get("to") or "").strip()
            if frm:
                parts.add(frm)
            if to:
                parts.add(to)
        for scene in list(first_scenes) + list(sex_scenes):
            if not isinstance(scene, dict):
                continue
            for p in scene.get("participants") or []:
                p_name = str(p or "").strip()
                if p_name:
                    parts.add(p_name)
        return parts

    participants = _collect_participants()

    # Add missing characters referenced elsewhere
    for p in sorted(participants):
        if p not in name_set:
            characters.append({
                "name": p,
                "gender": "unknown",
                "identity": "",
                "personality": "",
                "sexual_preferences": ""
            })
            name_set.add(p)
            errors.append(f"added missing character: {p}")

    # Build relationship keys to avoid duplicates (undirected)
    rel_keys = set()
    cleaned_rels = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        frm = str(rel.get("from") or "").strip()
        to = str(rel.get("to") or "").strip()
        if not frm or not to:
            continue
        key = tuple(sorted([frm, to]))
        if key in rel_keys:
            continue
        rel_keys.add(key)
        cleaned_rels.append(rel)
    relationships = cleaned_rels

    # Auto-add relationships from sex scenes (pairwise)
    for scene in sex_scenes:
        if not isinstance(scene, dict):
            continue
        participants_list = [str(p).strip() for p in scene.get("participants") or [] if str(p).strip()]
        if len(participants_list) < 2:
            continue
        for i in range(len(participants_list)):
            for j in range(i + 1, len(participants_list)):
                a, b = participants_list[i], participants_list[j]
                key = tuple(sorted([a, b]))
                if key in rel_keys:
                    continue
                rel_keys.add(key)
                relationships.append({
                    "from": a,
                    "to": b,
                    "type": "性关系",
                    "start_way": "性场景自动补全",
                    "description": "auto-added from sex scene"
                })
                errors.append(f"added missing relationship: {a} - {b}")

    data["characters"] = characters
    data["relationships"] = relationships
    return data, errors



@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _validate_api_url(api_url: str) -> str:
    url = (api_url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="API URL必须是http/https且包含主机，例如：https://example.com/v1")
    return url.rstrip("/")


def _safe_novel_path(base_path: Path, user_path: str) -> Path:
    base = base_path.resolve()
    raw = (user_path or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="路径不能为空")

    try:
        candidate = (base / raw).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="非法路径")

    try:
        candidate.relative_to(base)
    except Exception:
        raise HTTPException(status_code=403, detail="非法路径")

    if candidate.suffix.lower() != ".txt":
        raise HTTPException(status_code=400, detail="仅支持.txt文件")

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    return candidate


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/config")
def get_server_config():
    return {
        "api_url": os.getenv("API_BASE_URL", ""),
        "model": os.getenv("MODEL_NAME", "")
    }


@app.get("/api/novels")
def scan_novels():
    """递归扫描所有.txt小说文件"""
    if not DEFAULT_NOVEL_PATH.exists():
        raise HTTPException(status_code=400, detail=f"小说目录不存在: {DEFAULT_NOVEL_PATH}（可通过NOVEL_PATH配置）")

    base_path = str(DEFAULT_NOVEL_PATH)

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
    full_path = _safe_novel_path(DEFAULT_NOVEL_PATH, path)

    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")

        return {
            "name": full_path.name,
            "path": str(Path(path).as_posix()),
            "content": content,
            "length": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取失败: {str(e)}")


@app.get("/api/test-connection")
def test_connection():
    """测试API连接"""
    api_url, api_key, model = _get_llm_config()

    try:
        response = requests.post(
            f"{api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
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
    api_url, api_key, model = _get_llm_config()

    prompt_v1 = f"""
As a professional literary analyst specializing in adult fiction, analyze this novel comprehensively.

## Analysis Requirements

### 0. NOVEL METADATA
Extract basic novel information:
- World setting/background (genre, time period, universe type)
- World tags: short tags array (e.g., "现代都市", "校园", "豪门", "修仙", "科幻")
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
- **CRITICAL - FIRST-PERSON NARRATOR**: Many Chinese adult novels use first-person narration ("我"). If the narrator participates in ANY sexual activity, they MUST be listed as a character.
  - Determine their name/alias from how others address them (e.g., "哥哥", "老公", "男友", name, or simply "主角(哥哥)" / "主角(男主)" if no specific name).
  - Infer gender from context (pronouns, how addressed, role in sex scenes). Default to male if addressed as 哥哥/兄长/老公.
  - DO NOT omit the narrator just because they use "我". The narrator is a real character.

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

### 7. THUNDERZONE DETECTION (雷点检测)
Identify all potential "thunderzones" (deal-breakers) that might upset readers.
For each thunderzone found, provide: type, severity, characters involved, chapter location, and description.

雷点类型定义:
- 绿帽/Cuckold: Male character's partner has sex with others (willingly, coerced, or unknowingly)
- NTR (Netorare): Protagonist's romantic partner/lover/spouse is taken by another character
- 女性舔狗/Female Doormat: Female character who is excessively submissive, desperately pursues a man with no dignity
- 恶堕/Fall from Grace: A character who was pure/virtuous/innocent becomes corrupted, sexually liberated, or morally degraded
- 其他雷点/Other: Any other content that might be a deal-breaker (例如: 乱伦、SM程度过重、角色死亡等)

Severity 判定标准:
- 高/High: 核心剧情涉及，影响主角或主要配角，涉及详细描写
- 中/Medium: 支线剧情涉及，影响次要角色，有一定描写
- 低/Low: 背景提及、回忆片段、一笔带过

## Output Format (JSON ONLY)

### STRICT JSON OUTPUT RULES (MUST FOLLOW)
- Return ONLY one JSON object. No extra text, no explanations.
- Final output MUST start with `{{` and end with `}}`.
- Must be valid JSON: double quotes for keys/strings, no trailing commas, no comments, no NaN/Infinity.
- Do NOT output `null` for required arrays/objects. Use `[]`, `{{}}`, or `""`.
- Required top-level keys (MUST exist even if empty):
  - `novel_info`, `characters`, `relationships`, `first_sex_scenes`, `sex_scenes`, `evolution`, `summary`, `thunderzones`, `thunderzone_summary`
- If you are unsure about any field, keep the key and use empty values; do not omit keys.

### Schema skeleton (reference only; your FINAL answer must NOT include code fences)
{{
  "novel_info": {{
    "world_setting": "",
    "world_tags": [],
    "chapter_count": 0,
    "is_completed": false,
    "completion_note": ""
  }},
  "characters": [],
  "relationships": [],
  "first_sex_scenes": [],
  "sex_scenes": {{
    "total_count": 0,
    "scenes": []
  }},
  "evolution": [],
  "summary": "",
  "thunderzones": [],
  "thunderzone_summary": ""
}}

### Field requirements (when items exist)
- `characters[i]` MUST include: `name`, `gender`, `identity`, `personality`, `sexual_preferences`.
  - For FEMALE characters also include `lewdness_score` (1-100 integer) and `lewdness_analysis`.
- `relationships[i]` MUST include: `from`, `to`, `type`, `start_way`, `description` (all strings).
- `first_sex_scenes[i]` MUST include: `participants` (non-empty string array), `chapter`, `location`, `description`.
- `sex_scenes.scenes[i]` MUST include: `chapter`, `participants` (non-empty string array), `location`, `description`.
- `evolution[i]` MUST include: `chapter`, `stage`, `description`.
- `thunderzones[i]` MUST include: `type`, `severity` (高/中/低), `description`, `involved_characters` (string array), `chapter_location`, `relationship_context`.

### If you cannot produce valid JSON
Return the schema skeleton EXACTLY (with empty arrays/strings) and nothing else.

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

    for style_name, prompt in prompts:
        try:
            content, _raw = call_llm_with_response(api_url, api_key, model, prompt, temperature=0.7)
            analysis = extract_json_from_response(content)

            if analysis and ('characters' in analysis or 'sex_scenes' in analysis):
                break
            else:
                last_error = f"数据格式异常(内容长:{len(content)})"
                raw_response = content[:1000]
        except LLMCallError as e:
            last_error = str(e)
            if e.raw_response:
                raw_response = e.raw_response
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if not analysis:
        error_msg = f"分析失败: {last_error}"
        if raw_response and DEBUG:
            error_msg += f"\n\n原始响应:\n{raw_response[:2000]}"
        elif "返回内容过短" in last_error:
            error_msg += "\n\n原始响应内容太短，API可能拦截了请求"

        raise HTTPException(status_code=422, detail=error_msg)
    analysis = _ensure_analysis_defaults(analysis)

    # Local schema validation & reconciliation only (single LLM call)
    analysis, _ = _validate_and_fix_analysis(analysis)
    analysis, _ = _reconcile_entities(analysis)
    analysis, _ = _validate_and_fix_analysis(analysis)

    if not analysis.get("characters"):
        raise HTTPException(status_code=422, detail="分析失败: 无有效角色（模型输出无法修复）")
    return {"analysis": analysis}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.getenv("PORT", "6103"))
    log_level = os.getenv("LOG_LEVEL", "warning")
    display_host = "localhost" if host in {"0.0.0.0", "::"} else host
    print(f"\n  ➜  Local:   http://{display_host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
