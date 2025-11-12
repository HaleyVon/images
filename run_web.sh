#!/bin/bash
# 통합 웹 UI 실행 스크립트

echo "===================================="
echo "웨딩드레스 AI 시스템 시작"
echo "===================================="
echo ""

# 환경변수 확인
if [ ! -f .env ]; then
    echo "⚠️  경고: .env 파일이 없습니다."
    echo "   .env.example을 복사하여 .env 파일을 생성하고 API 키를 설정하세요."
    echo ""
    echo "   cp .env.example .env"
    echo ""
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 패키지 설치 확인
echo "📦 패키지 설치 확인 중..."

missing_packages=()

if ! python -c "import streamlit" 2>/dev/null; then
    missing_packages+=("streamlit")
fi

if ! python -c "import anthropic" 2>/dev/null; then
    missing_packages+=("anthropic")
fi

if ! python -c "from google import genai" 2>/dev/null; then
    missing_packages+=("google-genai")
fi

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "⚠️  다음 패키지가 설치되어 있지 않습니다: ${missing_packages[*]}"
    echo "   다음 명령어로 설치하세요:"
    echo ""
    echo "   pip install -r requirements.txt"
    echo ""
    exit 1
fi

echo "✅ 모든 패키지가 설치되어 있습니다."
echo ""

# 사용 가능한 UI 선택
echo "🎨 실행할 UI를 선택하세요:"
echo "1) 통합 UI (드레스 분석 + Virtual Try-On)"
echo "2) Virtual Try-On 전용 UI"
echo "3) 기존 드레스 분석 UI"
echo ""
read -p "선택 (1-3, 기본값: 1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo "🚀 통합 UI 시작..."
        streamlit run app_integrated.py
        ;;
    2)
        echo "🚀 Virtual Try-On UI 시작..."
        streamlit run app_tryon.py
        ;;
    3)
        echo "🚀 드레스 분석 UI 시작..."
        streamlit run app.py
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac
