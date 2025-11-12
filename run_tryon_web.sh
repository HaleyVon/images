#!/bin/bash
# Virtual Try-On 웹 UI 실행 스크립트

echo "=================================="
echo "Virtual Try-On 웹 UI 시작"
echo "=================================="
echo ""

# 환경변수 확인
if [ ! -f .env ]; then
    echo "⚠️  경고: .env 파일이 없습니다."
    echo "   .env.example을 복사하여 .env 파일을 생성하고 API 키를 설정하세요."
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 패키지 설치 확인
echo "📦 패키지 설치 확인 중..."
if ! python -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Streamlit이 설치되어 있지 않습니다."
    echo "   다음 명령어로 설치하세요: pip install -r requirements.txt"
    exit 1
fi

if ! python -c "from google import genai" 2>/dev/null; then
    echo "⚠️  google-genai가 설치되어 있지 않습니다."
    echo "   다음 명령어로 설치하세요: pip install -r requirements.txt"
    exit 1
fi

echo "✅ 모든 패키지가 설치되어 있습니다."
echo ""

# Streamlit 실행
echo "🚀 Streamlit 서버 시작..."
echo "   브라우저에서 자동으로 열립니다."
echo "   종료하려면 Ctrl+C를 누르세요."
echo ""

streamlit run app_tryon.py
