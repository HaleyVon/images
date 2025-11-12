#!/usr/bin/env python3
"""
Virtual Try-On Web UI (Streamlit)
웹에서 Virtual Try-On을 테스트할 수 있는 UI
"""

import os
import io
import base64
from pathlib import Path
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Virtual Try-On 모듈 임포트
from virtual_tryon import VirtualTryOn
from image_validator import ImageValidator

load_dotenv()


def main():
    st.set_page_config(
        page_title="Virtual Try-On",
        page_icon="👗",
        layout="wide"
    )

    st.title("👗 Virtual Try-On")
    st.caption("Gemini를 활용한 AI 가상 피팅 시스템")

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")

        gemini_api_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="빈 경우 .env의 환경변수를 사용합니다."
        )

        st.divider()

        # 모드 선택
        mode = st.radio(
            "모드 선택",
            ["기본 모드", "웨딩드레스 모드", "반복 개선 모드"],
            help="웨딩드레스 모드는 웨딩드레스에 최적화된 고품질 결과를 제공합니다."
        )

        # 반복 개선 모드 설정
        iterations = 2
        if mode == "반복 개선 모드":
            iterations = st.slider(
                "반복 횟수",
                min_value=1,
                max_value=3,
                value=2,
                help="반복 횟수가 많을수록 품질이 향상되지만 시간이 더 걸립니다."
            )

        st.divider()
        st.markdown("### 📖 사용 방법")
        st.markdown("""
1. 사람 이미지 업로드
2. 의류 이미지 업로드
3. 모드 선택
4. [Virtual Try-On 실행] 클릭
5. 결과 확인 및 다운로드
        """)

        st.divider()
        st.markdown("### 💡 팁")
        st.markdown("""
- 정면을 향한 전신 사진이 가장 좋습니다
- 밝고 깨끗한 배경 권장
- 고해상도 이미지 사용 권장
- 웨딩드레스는 '웨딩드레스 모드' 사용
        """)

    # 메인 영역
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

            # 이미지 검증 버튼
            if st.button("🔍 사람 이미지 검증", key="validate_person"):
                with st.spinner("이미지 검증 중..."):
                    try:
                        validator = ImageValidator(api_key=gemini_api_key or None)

                        # 임시 파일로 저장
                        temp_path = Path("temp_person.jpg")
                        person_image.save(temp_path, format="JPEG")

                        result = validator.validate_person_image(temp_path)

                        # 임시 파일 삭제
                        temp_path.unlink(missing_ok=True)

                        if result.is_person:
                            st.success("✅ 유효한 사람 이미지입니다!")
                            st.info(f"**설명:** {result.description}")

                            if not result.body_visible:
                                st.warning("⚠️ 신체가 명확하게 보이지 않습니다.")
                            if not result.pose_suitable:
                                st.warning("⚠️ 포즈가 Virtual Try-On에 적합하지 않을 수 있습니다.")
                        else:
                            st.error("❌ 사람 이미지가 아닙니다.")

                    except Exception as e:
                        st.error(f"검증 실패: {e}")

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

            # 이미지 검증 버튼
            if st.button("🔍 의류 이미지 검증", key="validate_clothing"):
                with st.spinner("이미지 검증 중..."):
                    try:
                        validator = ImageValidator(api_key=gemini_api_key or None)

                        # 임시 파일로 저장
                        temp_path = Path("temp_clothing.jpg")
                        clothing_image.save(temp_path, format="JPEG")

                        result = validator.validate_clothing_image(temp_path)

                        # 임시 파일 삭제
                        temp_path.unlink(missing_ok=True)

                        if result.is_clothing:
                            st.success("✅ 유효한 의류 이미지입니다!")
                            st.info(f"""
**타입:** {result.clothing_type}
**설명:** {result.description}
**색상:** {result.color}
**패턴:** {result.pattern}
                            """)
                        else:
                            st.error("❌ 의류 이미지가 아닙니다.")

                    except Exception as e:
                        st.error(f"검증 실패: {e}")

    st.divider()

    # Virtual Try-On 실행
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
                    # VirtualTryOn 인스턴스 생성
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
                            # base64인 경우
                            image_bytes = base64.b64decode(image_data)
                            result_image = Image.open(io.BytesIO(image_bytes))

                        # 3단 비교 (원본 사람, 원본 의류, 결과)
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
                            # 이미지를 bytes로 변환
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

                        # 추가 정보 표시 (있는 경우)
                        if "person" in result and "clothing" in result:
                            st.divider()
                            st.subheader("📊 분석 정보")

                            col_info1, col_info2 = st.columns(2)

                            with col_info1:
                                st.markdown("**👤 사람 정보**")
                                person_info = result["person"]
                                st.text(person_info.get("description", ""))

                            with col_info2:
                                st.markdown("**👗 의류 정보**")
                                clothing_info = result["clothing"]
                                st.text(f"타입: {clothing_info.get('clothing_type', '')}")
                                st.text(f"설명: {clothing_info.get('description', '')}")

                        # 프롬프트 표시 (있는 경우)
                        if "prompt" in result:
                            with st.expander("📝 사용된 프롬프트 보기"):
                                st.code(result["prompt"], language="text")

                    else:
                        st.error(f"❌ Virtual Try-On 실패: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    st.error(f"❌ 오류 발생: {e}")
                    import traceback
                    with st.expander("상세 오류 로그"):
                        st.code(traceback.format_exc())

    else:
        st.info("👆 사람 이미지와 의류 이미지를 모두 업로드하세요.")

    # 푸터
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray;'>
    <p>Powered by Google Gemini API | Built with Streamlit</p>
    <p>© 2024 Wedding Dress AI System</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
