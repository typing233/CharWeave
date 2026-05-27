#!/bin/bash
set -e

echo "=== CharWeave - 书籍人物关系图谱工具 ==="
echo ""

# Backend
echo "[1/4] 设置后端环境..."
cd "$(dirname "$0")/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
else
    source venv/bin/activate
    # Install any new dependencies
    pip install -r requirements.txt -q
fi

echo "[2/4] 下载 NLI 模型（首次运行需要几分钟）..."
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
model_name = 'cross-encoder/nli-deberta-v3-base'
try:
    AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    print('  模型已缓存，跳过下载。')
except:
    print('  正在下载模型...')
    AutoTokenizer.from_pretrained(model_name)
    AutoModelForSequenceClassification.from_pretrained(model_name)
    print('  模型下载完成。')
"

echo "[3/4] 启动后端 (FastAPI, port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300 &
BACKEND_PID=$!

# Frontend
echo "[4/4] 启动前端 (Vite, port 5173)..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== 服务已启动 ==="
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
