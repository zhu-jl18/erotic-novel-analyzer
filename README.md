# 小说分析器

基于LLM的小说分析工具 - 剧情高潮、人物关系、情感曲线可视化

## 功能特性

- 自动扫描本地小说文件夹
- 支持嵌套子文件夹
- LLM智能分析：人物关系、剧情高潮、情感曲线
- 可视化展示：力导向关系图、情感曲线图、高潮时间线
- 支持配置任意OpenAI兼容API

## 使用方法

### 1. 安装依赖

```bash
# 创建虚拟环境（已内置）
novel-analyzer\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API

编辑 `.env` 文件，填入你的API信息：

```env
API_BASE_URL=https://your-api.com/v1
API_KEY=sk-your-api-key
MODEL_NAME=gpt-4o
```

或者在浏览器界面中直接填写并保存。

### 3. 启动服务

**Windows (使用提供的脚本):**

```bash
start.bat
```

**手动启动:**

```bash
python backend.py
```

### 4. 使用

1. 打开浏览器访问 `http://localhost:8000`
2. 填写API配置并测试连接
3. 选择左侧小说文件
4. 点击"开始分析"
5. 查看分析结果，支持多个Tab切换

## 配置说明

| 配置项       | 说明     | 示例                   |
| ------------ | -------- | ---------------------- |
| API_BASE_URL | API地址  | https://juya.owl,ci/v1 |
| API_KEY      | API密钥  | sk-xxx                 |
| MODEL_NAME   | 模型名称 | DeepSeek-V3.1-Terminus |

## 目录结构

```
novel-analyzer/
├── backend.py          # FastAPI后端
├── .env                # API配置
├── requirements.txt    # 依赖列表
├── README.md           # 说明文档
├── templates/
│   └── index.html      # 前端页面
├── static/
│   ├── style.css       # 样式
│   └── chart-view.js   # 可视化逻辑
└── start.bat           # 启动脚本
```

## 依赖

- Python 3.8+
- fastapi
- uvicorn
- python-multipart
- jinja2
- python-dotenv
- requests
