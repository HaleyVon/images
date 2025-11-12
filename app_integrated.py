#!/usr/bin/env python3
"""
통합 웨딩드레스 AI 시스템 Web UI
드레스 분석 + Virtual Try-On 통합
"""

import os
import io
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# 드레스 분석 모듈
from dress_prompt_generator import DressPromptGenerator

# Virtual Try-On 모듈
from virtual_tryon import VirtualTryOn
from image_validator import ImageValidator

load_dotenv()


def dress_analysis_tab():
    """드레스 분석 탭"""
    st.header("👗 드레스 이미지 분석")
    st.caption("드레스 이미지를 분석하여 상세한 스키마를 생성합니다.")

    with st.sidebar:
        st.subheader("설정")
        anthropic_api_key = st.text_input(
            "ANTHROPIC_API_KEY",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Claude API 키"
        )

    # 이미지 업로드
    uploaded_file = st.file_uploader(
        "드레스 이미지를 업로드하세요",
        type=["png", "jpg", "jpeg"],
        key="dress_analysis_upload"
    )

    if uploaded_file:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(image, caption="업로드된 이미지", use_container_width=True)

        with col2:
            if st.button("🔍 드레스 분석 시작", type="primary", use_container_width=True):
                with st.spinner("드레스 분석 중..."):
                    try:
                        # 임시 파일로 저장
                        temp_path = Path("temp_dress_analysis.jpg")
                        image.save(temp_path, format="JPEG")

                        # 분석 수행
                        generator = DressPromptGenerator(api_key=anthropic_api_key or None)
                        result = generator.analyze_dress_image(str(temp_path))

                        # 임시 파일 삭제
                        temp_path.unlink(missing_ok=True)

                        st.success("✅ 분석 완료!")

                        # 결과 표시
                        st.subheader("📊 분석 결과")

                        # 스키마 표시
                        schema = result.get("schema", {})

                        col_info1, col_info2 = st.columns(2)

                        with col_info1:
                            st.markdown("**기본 정보**")
                            st.text(f"ID: {schema.get('id', '')}")
                            st.text(f"이름: {schema.get('name', '')}")
                            st.text(f"색상: {schema.get('color', '')}")

                        with col_info2:
                            st.markdown("**스타일 정보**")
                            st.text(f"라인: {', '.join(schema.get('line', []))}")
                            st.text(f"소재: {', '.join(schema.get('material', []))}")
                            st.text(f"넥라인: {', '.join(schema.get('neckline', []))}")

                        st.divider()

                        col_detail1, col_detail2 = st.columns(2)

                        with col_detail1:
                            st.markdown("**디테일**")
                            details = schema.get('detail', [])
                            if details:
                                for detail in details:
                                    st.text(f"• {detail}")
                            else:
                                st.text("없음")

                        with col_detail2:
                            st.markdown("**키워드**")
                            keywords = schema.get('keyword', [])
                            if keywords:
                                for keyword in keywords:
                                    st.text(f"• {keyword}")
                            else:
                                st.text("없음")

                        # JSON 다운로드
                        st.divider()
                        json_str = json.dumps(result, ensure_ascii=False, indent=2)

                        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
                        with col_dl2:
                            st.download_button(
                                label="📥 JSON 다운로드",
                                data=json_str.encode('utf-8'),
                                file_name=f"dress_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )

                    except Exception as e:
                        st.error(f"❌ 분석 실패: {e}")
                        import traceback
                        with st.expander("상세 오류 로그"):
                            st.code(traceback.format_exc())


def virtual_tryon_tab():
    """Virtual Try-On 탭"""
    st.header("✨ Virtual Try-On")
    st.caption("AI 가상 피팅으로 드레스를 입어보세요!")

    with st.sidebar:
        st.subheader("설정")
        gemini_api_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Gemini API 키"
        )

        st.divider()

        mode = st.radio(
            "모드 선택",
            ["기본 모드", "웨딩드레스 모드", "반복 개선 모드"],
            help="웨딩드레스 모드는 웨딩드레스에 최적화된 고품질 결과를 제공합니다."
        )

        iterations = 2
        if mode == "반복 개선 모드":
            iterations = st.slider(
                "반복 횟수",
                min_value=1,
                max_value=3,
                value=2,
                help="반복 횟수가 많을수록 품질이 향상되지만 시간이 더 걸립니다."
            )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 사람 이미지")
        person_image_file = st.file_uploader(
            "사람 이미지를 업로드하세요",
            type=["png", "jpg", "jpeg"],
            key="person_image",
            help="전신 또는 상반신이 명확하게 보이는 정면 사진"
        )

        if person_image_file:
            person_image = Image.open(person_image_file)
            st.image(person_image, caption="업로드된 사람 이미지", use_container_width=True)

    with col2:
        st.subheader("👗 의류 이미지")
        clothing_image_file = st.file_uploader(
            "의류 이미지를 업로드하세요",
            type=["png", "jpg", "jpeg"],
            key="clothing_image",
            help="드레스 전체가 명확하게 보이는 이미지"
        )

        if clothing_image_file:
            clothing_image = Image.open(clothing_image_file)
            st.image(clothing_image, caption="업로드된 의류 이미지", use_container_width=True)

    st.divider()

    if person_image_file and clothing_image_file:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

        with col_btn2:
            run_tryon = st.button(
                "🎯 Virtual Try-On 실행",
                type="primary",
                use_container_width=True
            )

        if run_tryon:
            with st.spinner("Virtual Try-On 생성 중... (약 10-30초 소요)"):
                try:
                    tryon = VirtualTryOn(api_key=gemini_api_key or None)

                    # 임시 파일로 저장
                    person_temp = Path("temp_person_tryon.jpg")
                    clothing_temp = Path("temp_clothing_tryon.jpg")

                    person_image.save(person_temp, format="JPEG")
                    clothing_image.save(clothing_temp, format="JPEG")

                    # Virtual Try-On 수행
                    if mode == "반복 개선 모드":
                        result = tryon.iterative_try_on(
                            str(person_temp),
                            str(clothing_temp),
                            iterations=iterations
                        )
                    else:
                        style = "wedding" if mode == "웨딩드레스 모드" else "default"
                        result = tryon.process_with_validation(
                            str(person_temp),
                            str(clothing_temp),
                            style=style
                        )

                    # 임시 파일 삭제
                    person_temp.unlink(missing_ok=True)
                    clothing_temp.unlink(missing_ok=True)

                    if result["success"]:
                        st.success("✅ Virtual Try-On 완료!")

                        # 결과 이미지 표시
                        st.subheader("🎨 결과 이미지")

                        # bytes를 PIL Image로 변환
                        image_data = result["image"]
                        if isinstance(image_data, bytes):
                            result_image = Image.open(io.BytesIO(image_data))
                        else:
                            image_bytes = base64.b64decode(image_data)
                            result_image = Image.open(io.BytesIO(image_bytes))

                        # 3단 비교
                        col_result1, col_result2, col_result3 = st.columns(3)

                        with col_result1:
                            st.image(person_image, caption="원본 사람 이미지", use_container_width=True)

                        with col_result2:
                            st.image(clothing_image, caption="원본 의류 이미지", use_container_width=True)

                        with col_result3:
                            st.image(result_image, caption="Virtual Try-On 결과", use_container_width=True)

                        # 다운로드 버튼
                        st.divider()
                        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])

                        with col_dl2:
                            buf = io.BytesIO()
                            result_image.save(buf, format="JPEG", quality=95)
                            buf.seek(0)

                            st.download_button(
                                label="📥 결과 이미지 다운로드",
                                data=buf,
                                file_name="virtual_tryon_result.jpg",
                                mime="image/jpeg",
                                use_container_width=True
                            )

                    else:
                        st.error(f"❌ Virtual Try-On 실패: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    st.error(f"❌ 오류 발생: {e}")
                    import traceback
                    with st.expander("상세 오류 로그"):
                        st.code(traceback.format_exc())

    else:
        st.info("👆 사람 이미지와 의류 이미지를 모두 업로드하세요.")


def main():
    """메인 함수"""
    st.set_page_config(
        page_title="웨딩드레스 AI 시스템",
        page_icon="💒",
        layout="wide"
    )

    st.title("💒 웨딩드레스 AI 시스템")
    st.caption("드레스 분석 + Virtual Try-On 통합 시스템")

    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "👗 드레스 분석",
        "✨ Virtual Try-On",
        "📖 사용 가이드"
    ])

    with tab1:
        dress_analysis_tab()

    with tab2:
        virtual_tryon_tab()

    with tab3:
        st.header("📖 사용 가이드")

        st.markdown("""
## 🎯 기능 소개

### 1. 드레스 이미지 분석
드레스 이미지를 업로드하면 AI가 자동으로 분석하여 다음 정보를 추출합니다:
- 라인 (A라인, 머메이드, 볼가운 등)
- 소재 (레이스, 새틴, 튤 등)
- 색상
- 넥라인 (오프숄더, 브이넥 등)
- 소매 (롱슬리브, 슬리브리스 등)
- 디테일 (비즈, 시퀸, 코르셋 등)
- 키워드 (로맨틱, 우아한 등)

### 2. Virtual Try-On
사람 이미지와 드레스 이미지를 업로드하면 AI가 가상 피팅 결과를 생성합니다.

**3가지 모드:**
- **기본 모드**: 빠른 결과 생성
- **웨딩드레스 모드**: 웨딩드레스에 최적화된 고품질 결과
- **반복 개선 모드**: 최고 품질 (시간 소요)

## 💡 사용 팁

### 드레스 분석
- 드레스가 전체적으로 명확하게 보이는 이미지 사용
- 밝은 배경 권장
- 고해상도 이미지 권장

### Virtual Try-On
- **사람 이미지:**
  - 정면을 향한 전신 또는 상반신 사진
  - 밝고 깨끗한 배경
  - 중립적인 포즈 (팔을 옆으로)

- **의류 이미지:**
  - 드레스 전체가 보이는 사진
  - 디테일이 선명하게 보이는 고화질
  - 평면 또는 착용 상태 모두 가능

## 🔑 API 키 설정

각 탭의 사이드바에서 API 키를 입력하거나, `.env` 파일에 저장할 수 있습니다:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key
```

**API 키 발급:**
- [Anthropic Console](https://console.anthropic.com/)
- [Google AI Studio](https://aistudio.google.com/app/apikey)

## ⚠️ 주의사항

- 초상권 및 저작권에 주의하세요
- 상업적 사용 시 해당 API의 이용 약관을 확인하세요
- 생성된 이미지는 참고용으로만 사용하세요

## 🆘 문제 해결

**"API 키가 설정되지 않았습니다"**
- 사이드바에서 API 키를 입력하거나
- `.env` 파일을 생성하여 API 키를 저장하세요

**"이미지 검증 실패"**
- 사람이 명확하게 보이는 이미지를 사용하세요
- 의류가 전체적으로 보이는 이미지를 사용하세요

**"Virtual Try-On 실패"**
- API 키가 올바른지 확인하세요
- 이미지 품질을 확인하세요
- 잠시 후 다시 시도하세요
        """)

    # 푸터
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray;'>
    <p>Powered by Anthropic Claude & Google Gemini | Built with Streamlit</p>
    <p>© 2024 Wedding Dress AI System</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
