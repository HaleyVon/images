#!/usr/bin/env python3
"""
Streamlit UI for Wedding Dress Analyzer
이미지를 업로드하면 Anthropic 기반 분석기로 프롬프트/스키마를 생성하고,
결과를 로컬 JSONL 파일에 누적 저장합니다. 테이블로 조회/복사/삭제/다운로드를 지원합니다.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from dress_prompt_generator import DressPromptGenerator
from PIL import Image


def get_default_save_dir() -> Path:
    # 홈 디렉토리 하위의 고정 경로 기본값
    home = Path.home()
    return home / "wedding-dress-analyzer" / "data"


def resolve_store_path(base_dir: Path) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "results.jsonl"


def get_dress_images_dir() -> Path:
    # dress-images 폴더 경로
    return Path(__file__).parent / "dress-images"


def save_uploaded_file(file, target_name: str = None) -> Path:
    """
    업로드된 파일을 dress-images 폴더에 저장
    
    Args:
        file: Streamlit 업로드 파일 객체
        target_name: 저장할 파일명 (None이면 원본 이름 사용)
    
    Returns:
        저장된 파일의 경로
    """
    dress_dir = get_dress_images_dir()
    dress_dir.mkdir(exist_ok=True)
    
    if target_name is None:
        target_name = file.name
    
    target_path = dress_dir / target_name
    
    # 파일명 중복 처리
    counter = 1
    original_target = target_path
    while target_path.exists():
        stem = original_target.stem
        suffix = original_target.suffix
        target_path = dress_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    with open(target_path, "wb") as out:
        out.write(file.getbuffer())
    
    return target_path


def load_store(store_path: Path) -> List[Dict[str, Any]]:
    if not store_path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with open(store_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # 손상된 라인은 무시
                continue
    return rows


def append_store(store_path: Path, row: Dict[str, Any]) -> None:
    with open(store_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def overwrite_store(store_path: Path, rows: List[Dict[str, Any]]) -> None:
    with open(store_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate_dress_name_and_id(
    line: List[str],
    detail: List[str],
    material: List[str],
    existing_names: set = None,
    existing_ids: set = None,
) -> tuple[str, str]:
    """
    드레스 이름과 ID를 자동 생성
    
    규칙:
    - name: "{ 라인_디테일(있을경우 대표적인거 1개)_소재 드레스 }" 형식
    - id: 동일한 규칙이지만 영문으로
    
    Args:
        line: 라인 리스트 (1개만 선택)
        detail: 디테일 리스트 (0~3개, 대표적인 것 1개만 사용)
        material: 소재 리스트 (1~2개, 첫 번째 것 사용)
        existing_names: 기존 이름 집합 (중복 체크용)
        existing_ids: 기존 ID 집합 (중복 체크용)
    
    Returns:
        (name, id) 튜플
    """
    from dress_prompt_generator import DressPromptGenerator
    
    # 한국어 -> 영문 변환 맵
    korean_to_english = DressPromptGenerator.KOREAN_TO_ENGLISH
    
    # 라인 (1개만)
    line_kr = line[0] if line else ""
    line_en = korean_to_english.get(line_kr, line_kr.lower().replace(" ", "-"))
    
    # 디테일 (대표적인 것 1개만, 있으면)
    detail_kr = ""
    detail_en = ""
    if detail:
        # 대표적인 디테일 선택 (우선순위: 비즈, 시퀸, 코르셋 등)
        priority_details = ["비즈", "시퀸", "코르셋", "드레이핑", "일루전 백", "아플리케 레이스"]
        for priority in priority_details:
            if priority in detail:
                detail_kr = priority
                detail_en = korean_to_english.get(priority, priority.lower().replace(" ", "-"))
                break
        if not detail_kr:
            # 우선순위에 없으면 첫 번째 것 사용
            detail_kr = detail[0]
            detail_en = korean_to_english.get(detail_kr, detail_kr.lower().replace(" ", "-"))
    
    # 소재 (1~2개 중 첫 번째 것)
    material_kr = material[0] if material else ""
    material_en = korean_to_english.get(material_kr, material_kr.lower().replace(" ", "-"))
    
    # name 생성
    if detail_kr:
        name = f"{line_kr}_{detail_kr}_{material_kr} 드레스"
    else:
        name = f"{line_kr}_{material_kr} 드레스"
    
    # id 생성 (영문)
    if detail_en:
        base_id = f"{line_en}_{detail_en}_{material_en}"
    else:
        base_id = f"{line_en}_{material_en}"
    
    # 중복 처리
    final_name = name
    final_id = base_id
    
    if existing_names is not None:
        counter = 1
        while final_name in existing_names:
            if detail_kr:
                final_name = f"{line_kr}_{detail_kr}_{material_kr}_{counter:02d} 드레스"
            else:
                final_name = f"{line_kr}_{material_kr}_{counter:02d} 드레스"
            counter += 1
    
    if existing_ids is not None:
        counter = 1
        while final_id in existing_ids:
            if detail_en:
                final_id = f"{line_en}_{detail_en}_{material_en}_{counter:02d}"
            else:
                final_id = f"{line_en}_{material_en}_{counter:02d}"
            counter += 1
    
    return final_name, final_id


def flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
    schema = record.get("schema", {}) or {}
    flat = {
        "id": record.get("id"),
        "created_at": record.get("created_at"),
        "image_name": record.get("image_name"),
        "original_name": record.get("original_name", ""),
        "file_path": record.get("file_path", ""),
        "prompt": record.get("prompt"),
        "name": schema.get("name"),
        "line": ", ".join(schema.get("line", []) or []),
        "material": ", ".join(schema.get("material", []) or []),
        "color": schema.get("color"),
        "neckline": ", ".join(schema.get("neckline", []) or []),
        "sleeve": ", ".join(schema.get("sleeve", []) or []),
        "keyword": ", ".join(schema.get("keyword", []) or []),
        "detail": ", ".join(schema.get("detail", []) or []),
        "dress_lengths": ", ".join(schema.get("dress_lengths", []) or []),
    }
    return flat


def main() -> None:
    st.set_page_config(page_title="Wedding Dress Analyzer", layout="wide")
    st.title("Wedding Dress Analyzer")
    st.caption("이미지 업로드 → 프롬프트/스키마 생성 → 로컬 저장/관리")

    with st.sidebar:
        st.header("설정")
        api_key = st.text_input(
            "ANTHROPIC_API_KEY",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="빈 경우 .env의 환경변수(있다면)를 사용합니다.",
        )
        default_dir = str(get_default_save_dir())
        base_dir_str = st.text_input(
            "저장 디렉토리",
            value=st.session_state.get("save_dir", default_dir),
            help="결과 JSONL을 누적 저장할 폴더 경로",
        )
        st.session_state["save_dir"] = base_dir_str
        save_dir = Path(base_dir_str).expanduser()
        store_path = resolve_store_path(save_dir)

        auto_analyze = st.checkbox("업로드 시 자동 분석/저장", value=True)
        auto_rename = st.checkbox("분석 후 파일명을 schema.name으로 변경", value=True)
        st.divider()
        view_mode = st.radio("보기 모드", ["플랫", "원본 JSON", "CSV"], index=0)
        st.divider()
        st.markdown(f"데이터 파일: `{store_path}`")
        st.markdown(f"이미지 저장 폴더: `{get_dress_images_dir()}`")

    st.subheader("이미지 업로드 및 분석")
    uploaded_files = st.file_uploader(
        "드레스 이미지 선택 (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )
    analyze_clicked = st.button("선택 이미지 분석 및 저장")

    # 자동 분석 조건: 자동 옵션이 켜져 있고, 업로드된 파일이 있으며, 중복 실행 방지
    if "_processed_names" not in st.session_state:
        st.session_state["_processed_names"] = set()

    trigger_auto = auto_analyze and uploaded_files and not analyze_clicked
    should_run = (analyze_clicked or trigger_auto) and uploaded_files

    if should_run:
        try:
            generator = DressPromptGenerator(api_key=api_key or None)
        except Exception as e:
            st.error(f"생성기 초기화 실패: {e}")
            st.stop()

        for file in uploaded_files:
            # 자동 실행 시 같은 파일명은 중복 처리하지 않음
            if trigger_auto and file.name in st.session_state["_processed_names"]:
                continue
            
            # 1. 먼저 원본 이름으로 dress-images 폴더에 저장
            original_name = file.name
            saved_path = save_uploaded_file(file, original_name)
            
            try:
                # 2. 저장된 파일로 분석 수행
                result = generator.analyze_dress_image(str(saved_path))
            except Exception as e:
                st.error(f"분석 실패({file.name}): {e}")
                saved_path.unlink(missing_ok=True)  # 분석 실패 시 저장된 파일 삭제
                continue

            # 3. 파일명 변경 처리
            new_name = original_name
            final_path = saved_path
            
            if auto_rename and result.get("schema", {}).get("id") or result.get("schema", {}).get("name"):
                schema_id = result.get("schema", {}).get("id")
                schema_name = result.get("schema", {}).get("name")
                # 파일 확장자 유지
                file_ext = Path(original_name).suffix
                base_new = schema_id or schema_name
                new_name = f"{base_new}{file_ext}"
                
                # dress-images 폴더 내에서 파일명 변경
                new_path = get_dress_images_dir() / new_name
                
                # 파일명 중복 처리
                counter = 1
                original_new_path = new_path
                while new_path.exists():
                    stem = original_new_path.stem
                    suffix = original_new_path.suffix
                    new_path = get_dress_images_dir() / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                try:
                    saved_path.rename(new_path)
                    final_path = new_path
                    st.success(f"파일명 변경: {original_name} → {new_path.name}")
                except Exception as e:
                    st.warning(f"파일명 변경 실패({original_name}): {e}")
                    new_name = original_name  # 변경 실패 시 원본 이름 사용

            record = {
                "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "image_name": Path(final_path).stem,  # 확장자 없는 파일명
                "original_name": original_name,  # 원본 파일명
                "file_path": str(final_path),  # 실제 파일 경로 (확장자 포함)
                "prompt": result.get("prompt"),
                "schema": result.get("schema"),
            }
            append_store(store_path, record)
            st.session_state["_processed_names"].add(file.name)

        st.success("분석 및 저장이 완료되었습니다.")

    # 이미지 보기 및 편집 UI
    st.divider()
    st.subheader("이미지 보기 및 편집")
    
    rows = load_store(store_path)
    if not rows:
        st.info("저장된 데이터가 없습니다. 이미지를 업로드하여 분석해 보세요.")
    else:
        # 편집 모드 진입 버튼
        if "edit_mode" not in st.session_state:
            st.session_state["edit_mode"] = False
        
        if "edit_image_index" not in st.session_state:
            st.session_state["edit_image_index"] = 0
        
        if "edit_records" not in st.session_state:
            st.session_state["edit_records"] = []
        
        if not st.session_state["edit_mode"]:
            if st.button("보기 및 편집 모드 시작", type="primary"):
                st.session_state["edit_mode"] = True
                st.session_state["edit_image_index"] = 0
                st.session_state["edit_records"] = rows.copy()
                st.rerun()
        
        if st.session_state["edit_mode"]:
            edit_records = st.session_state["edit_records"]
            current_index = st.session_state["edit_image_index"]
            
            if current_index < len(edit_records):
                current_record = edit_records[current_index]
                schema = current_record.get("schema", {})
                file_path = current_record.get("file_path", "")
                
                # 이미지 네비게이션
                col_nav_prev, col_nav_slider, col_nav_next = st.columns([1, 8, 1])
                
                with col_nav_prev:
                    if st.button("◀", key="nav_prev", disabled=(current_index == 0), use_container_width=True):
                        st.session_state["edit_image_index"] = current_index - 1
                        st.rerun()
                
                with col_nav_slider:
                    selected_index = st.slider(
                        "이미지 선택",
                        min_value=0,
                        max_value=len(edit_records) - 1,
                        value=current_index,
                        format=f"%d / {len(edit_records)}",
                        key="image_slider",
                        label_visibility="collapsed"
                    )
                    if selected_index != current_index:
                        st.session_state["edit_image_index"] = selected_index
                        st.rerun()
                
                with col_nav_next:
                    if st.button("▶", key="nav_next", disabled=(current_index >= len(edit_records) - 1), use_container_width=True):
                        st.session_state["edit_image_index"] = current_index + 1
                        st.rerun()
                
                # 진행 상황 표시
                st.progress((current_index + 1) / len(edit_records))
                st.caption(f"진행 상황: {current_index + 1} / {len(edit_records)}")
                
                # 왼쪽: 이미지, 오른쪽: 편집 UI
                col_image, col_edit = st.columns([1, 1])
                
                with col_image:
                    st.markdown("### 이미지")
                    if file_path and Path(file_path).exists():
                        try:
                            img = Image.open(file_path)
                            st.image(img, use_container_width=True)
                        except Exception as e:
                            st.error(f"이미지 로드 실패: {e}")
                    else:
                        st.warning("이미지 파일을 찾을 수 없습니다.")
                    
                    st.markdown(f"**파일명:** {current_record.get('image_name', '')}")
                    st.markdown(f"**ID:** {current_record.get('id', '')}")
                
                with col_edit:
                    st.markdown("### 데이터 편집")
                    
                    # 허용 어휘 목록 가져오기
                    allowed_lines = DressPromptGenerator.ALLOWED_LINES
                    allowed_materials = DressPromptGenerator.ALLOWED_MATERIALS
                    allowed_necklines = DressPromptGenerator.ALLOWED_NECKLINES
                    allowed_sleeves = DressPromptGenerator.ALLOWED_SLEEVES
                    allowed_keywords = DressPromptGenerator.ALLOWED_KEYWORDS
                    allowed_details = DressPromptGenerator.ALLOWED_DETAILS
                    allowed_dress_lengths = DressPromptGenerator.ALLOWED_DRESS_LENGTHS
                    
                    # 배열 필드 편집 (태그 버튼 형태) - 변수 정의를 먼저
                    current_line = schema.get("line", [])
                    current_material = schema.get("material", [])
                    current_neckline = schema.get("neckline", [])
                    current_sleeve = schema.get("sleeve", [])
                    current_keyword = schema.get("keyword", [])
                    current_detail = schema.get("detail", [])
                    current_dress_lengths = schema.get("dress_lengths", [])
                    
                    # 각 필드의 현재 선택 상태를 세션 상태로 관리
                    line_key = f"edit_line_{current_index}"
                    material_key = f"edit_material_{current_index}"
                    neckline_key = f"edit_neckline_{current_index}"
                    sleeve_key = f"edit_sleeve_{current_index}"
                    keyword_key = f"edit_keyword_{current_index}"
                    detail_key = f"edit_detail_{current_index}"
                    dress_lengths_key = f"edit_dress_lengths_{current_index}"
                    
                    # 세션 상태 초기화
                    if line_key not in st.session_state:
                        st.session_state[line_key] = set(current_line)
                    if material_key not in st.session_state:
                        st.session_state[material_key] = set(current_material)
                    if neckline_key not in st.session_state:
                        st.session_state[neckline_key] = set(current_neckline)
                    if sleeve_key not in st.session_state:
                        st.session_state[sleeve_key] = set(current_sleeve)
                    if keyword_key not in st.session_state:
                        st.session_state[keyword_key] = set(current_keyword)
                    if detail_key not in st.session_state:
                        st.session_state[detail_key] = set(current_detail)
                    if dress_lengths_key not in st.session_state:
                        st.session_state[dress_lengths_key] = set(current_dress_lengths)
                    
                    # 기본 정보 편집
                    col_title, col_regenerate, col_approve_top = st.columns([2, 1, 1])
                    with col_title:
                        st.markdown("**기본 정보**")
                    with col_regenerate:
                        regenerate_key = f"regenerate_{current_index}"
                        if st.button("🔄 재생성", key=regenerate_key, use_container_width=True):
                            # 현재 선택된 태그로 name과 id 재생성
                            selected_line = list(st.session_state[line_key])
                            selected_detail = list(st.session_state[detail_key])
                            selected_material = list(st.session_state[material_key])
                            
                            if selected_line and selected_material:
                                # 현재까지 편집된 레코드 확인
                                existing_names = set()
                                existing_ids = set()
                                for idx, record in enumerate(edit_records):
                                    if idx < current_index:
                                        rec_schema = record.get("schema", {})
                                        existing_name = rec_schema.get("name", "")
                                        existing_id = rec_schema.get("id", "")
                                        if existing_name:
                                            existing_names.add(existing_name)
                                        if existing_id:
                                            existing_ids.add(existing_id)
                                
                                auto_name, auto_id = generate_dress_name_and_id(
                                    selected_line,
                                    selected_detail,
                                    selected_material,
                                    existing_names,
                                    existing_ids,
                                )
                                
                                # 재생성된 값을 세션 상태에 저장
                                st.session_state[f"edit_id_{current_index}"] = auto_id
                                st.session_state[f"edit_name_{current_index}"] = auto_name
                                st.rerun()
                            else:
                                st.warning("라인과 소재를 선택해주세요.")
                    with col_approve_top:
                        approve_top_key = f"approve_top_{current_index}"
                        top_approve_clicked = st.button("✅ 승인", key=approve_top_key, type="primary", use_container_width=True)
                    
                    # name과 id 자동 생성 (미리보기)
                    selected_line = list(st.session_state[line_key])
                    selected_detail = list(st.session_state[detail_key])
                    selected_material = list(st.session_state[material_key])
                    
                    auto_name = ""
                    auto_id = ""
                    if selected_line and selected_material:
                        # 현재까지 편집된 레코드 확인
                        existing_names = set()
                        existing_ids = set()
                        for idx, record in enumerate(edit_records):
                            if idx < current_index:
                                rec_schema = record.get("schema", {})
                                existing_name = rec_schema.get("name", "")
                                existing_id = rec_schema.get("id", "")
                                if existing_name:
                                    existing_names.add(existing_name)
                                if existing_id:
                                    existing_ids.add(existing_id)
                        
                        auto_name, auto_id = generate_dress_name_and_id(
                            selected_line,
                            selected_detail,
                            selected_material,
                            existing_names,
                            existing_ids,
                        )
                    
                    # 세션 상태에서 값을 가져오거나 기본값 사용
                    id_input_key = f"edit_id_{current_index}"
                    name_input_key = f"edit_name_{current_index}"
                    
                    # ID와 이름을 컬럼으로 배치
                    col_id, col_name, col_color = st.columns(3)
                    with col_id:
                        # 초기값 설정: 세션 상태에 없으면 스키마 또는 자동 생성값 사용
                        if id_input_key not in st.session_state:
                            st.session_state[id_input_key] = schema.get("id", auto_id)
                        st.text_input(
                            "ID (자동 생성됨, 수정 가능)",
                            key=id_input_key,
                            help=f"자동 생성: {auto_id if auto_id else '라인과 소재를 선택하면 자동 생성됩니다'}"
                        )
                    with col_name:
                        # 초기값 설정: 세션 상태에 없으면 스키마 또는 자동 생성값 사용
                        if name_input_key not in st.session_state:
                            st.session_state[name_input_key] = schema.get("name", auto_name)
                        st.text_input(
                            "이름 (자동 생성됨, 수정 가능)",
                            key=name_input_key,
                            help=f"자동 생성: {auto_name if auto_name else '라인과 소재를 선택하면 자동 생성됩니다'}"
                        )
                    with col_color:
                        color_input_key = f"edit_color_{current_index}"
                        # 초기값 설정: 세션 상태에 없으면 스키마에서 가져오기
                        if color_input_key not in st.session_state:
                            st.session_state[color_input_key] = schema.get("color", "")
                        st.text_input(
                            "색상",
                            key=color_input_key
                        )
                    
                    # 세션 상태에서 실제 값 가져오기
                    edited_id = st.session_state.get(id_input_key, "")
                    edited_name = st.session_state.get(name_input_key, "")
                    edited_color = st.session_state.get(color_input_key, "")
                    
                    # CSS 스타일 추가 (버튼 크기 및 간격 줄이기)
                    st.markdown("""
                    <style>
                    .stButton > button {
                        margin: 0.1rem 0.1rem !important;
                        padding: 0.1rem 0.1rem !important;
                        font-size: 0.7rem !important;
                        min-height: 1.0rem !important;
                        height: auto !important;
                    }
                    .stButton > button p {
                        font-size: 0.7rem !important;
                    }
                    .stButton > button div {
                        font-size: 0.7rem !important;
                    }
                    div[data-testid="column"] {
                        padding: 0.1rem !important;
                    }
                    button[kind="primary"], button[kind="secondary"] {
                        font-size: 0.7rem !important;
                        padding: 0.1rem 0.1rem !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Line 필드 (1개만 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>라인</strong> (1개 선택)</p>", unsafe_allow_html=True)
                    cols_line = st.columns(8)
                    for idx, value in enumerate(allowed_lines):
                        with cols_line[idx % 8]:
                            is_selected = value in st.session_state[line_key]
                            if st.button(
                                value,
                                key=f"{line_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 선택 해제
                                    st.session_state[line_key].remove(value)
                                else:
                                    # 기존 선택 모두 제거하고 새 항목만 선택
                                    st.session_state[line_key].clear()
                                    st.session_state[line_key].add(value)
                                st.rerun()
                    
                    # Material 필드 (1~2개 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>소재</strong> (1~2개 선택)</p>", unsafe_allow_html=True)
                    cols_material = st.columns(8)
                    for idx, value in enumerate(allowed_materials):
                        with cols_material[idx % 8]:
                            is_selected = value in st.session_state[material_key]
                            if st.button(
                                value,
                                key=f"{material_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 최소 1개는 유지해야 하므로, 2개 이상일 때만 제거 가능
                                    if len(st.session_state[material_key]) > 1:
                                        st.session_state[material_key].remove(value)
                                else:
                                    # 최대 2개까지 선택 가능
                                    if len(st.session_state[material_key]) < 2:
                                        st.session_state[material_key].add(value)
                                    else:
                                        # 2개가 이미 선택되어 있으면, 가장 오래된 것 제거하고 새 항목 추가
                                        if len(st.session_state[material_key]) > 0:
                                            first_item = next(iter(st.session_state[material_key]))
                                            st.session_state[material_key].remove(first_item)
                                        st.session_state[material_key].add(value)
                                st.rerun()
                    
                    # Neckline 필드 (1개만 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>넥라인</strong> (1개 선택)</p>", unsafe_allow_html=True)
                    cols_neckline = st.columns(8)
                    for idx, value in enumerate(allowed_necklines):
                        with cols_neckline[idx % 8]:
                            is_selected = value in st.session_state[neckline_key]
                            if st.button(
                                value,
                                key=f"{neckline_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 선택 해제
                                    st.session_state[neckline_key].remove(value)
                                else:
                                    # 기존 선택 모두 제거하고 새 항목만 선택
                                    st.session_state[neckline_key].clear()
                                    st.session_state[neckline_key].add(value)
                                st.rerun()
                    
                    # Sleeve 필드 (1개만 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>소매</strong> (1개 선택)</p>", unsafe_allow_html=True)
                    cols_sleeve = st.columns(8)
                    for idx, value in enumerate(allowed_sleeves):
                        with cols_sleeve[idx % 8]:
                            is_selected = value in st.session_state[sleeve_key]
                            if st.button(
                                value,
                                key=f"{sleeve_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 선택 해제
                                    st.session_state[sleeve_key].remove(value)
                                else:
                                    # 기존 선택 모두 제거하고 새 항목만 선택
                                    st.session_state[sleeve_key].clear()
                                    st.session_state[sleeve_key].add(value)
                                st.rerun()
                    
                    # Keyword 필드 (1~3개 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>키워드</strong> (1~3개 선택)</p>", unsafe_allow_html=True)
                    cols_keyword = st.columns(8)
                    for idx, value in enumerate(allowed_keywords):
                        with cols_keyword[idx % 8]:
                            is_selected = value in st.session_state[keyword_key]
                            if st.button(
                                value,
                                key=f"{keyword_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 최소 1개는 유지해야 하므로, 2개 이상일 때만 제거 가능
                                    if len(st.session_state[keyword_key]) > 1:
                                        st.session_state[keyword_key].remove(value)
                                else:
                                    # 최대 3개까지 선택 가능
                                    if len(st.session_state[keyword_key]) < 3:
                                        st.session_state[keyword_key].add(value)
                                    else:
                                        # 3개가 이미 선택되어 있으면, 가장 오래된 것 제거하고 새 항목 추가
                                        if len(st.session_state[keyword_key]) > 0:
                                            first_item = next(iter(st.session_state[keyword_key]))
                                            st.session_state[keyword_key].remove(first_item)
                                        st.session_state[keyword_key].add(value)
                                st.rerun()
                    
                    # Detail 필드 (0~3개 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>디테일</strong> (0~3개 선택)</p>", unsafe_allow_html=True)
                    cols_detail = st.columns(8)
                    for idx, value in enumerate(allowed_details):
                        with cols_detail[idx % 8]:
                            is_selected = value in st.session_state[detail_key]
                            if st.button(
                                value,
                                key=f"{detail_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 선택 해제 가능
                                    st.session_state[detail_key].remove(value)
                                else:
                                    # 최대 3개까지 선택 가능
                                    if len(st.session_state[detail_key]) < 3:
                                        st.session_state[detail_key].add(value)
                                    else:
                                        # 3개가 이미 선택되어 있으면, 가장 오래된 것 제거하고 새 항목 추가
                                        if len(st.session_state[detail_key]) > 0:
                                            first_item = next(iter(st.session_state[detail_key]))
                                            st.session_state[detail_key].remove(first_item)
                                        st.session_state[detail_key].add(value)
                                st.rerun()
                    
                    # Dress Lengths 필드 (1개만 선택)
                    st.markdown("<p style='margin-bottom:0.3rem; font-size:0.9rem;'><strong>드레스 길이</strong> (1개 선택)</p>", unsafe_allow_html=True)
                    cols_dress_lengths = st.columns(8)
                    for idx, value in enumerate(allowed_dress_lengths):
                        with cols_dress_lengths[idx % 8]:
                            is_selected = value in st.session_state[dress_lengths_key]
                            if st.button(
                                value,
                                key=f"{dress_lengths_key}_btn_{value}",
                                type="primary" if is_selected else "secondary",
                                use_container_width=True,
                            ):
                                if is_selected:
                                    # 선택 해제
                                    st.session_state[dress_lengths_key].remove(value)
                                else:
                                    # 기존 선택 모두 제거하고 새 항목만 선택
                                    st.session_state[dress_lengths_key].clear()
                                    st.session_state[dress_lengths_key].add(value)
                                st.rerun()
                    
                    st.divider()
                    
                    # 승인 버튼
                    bottom_approve_clicked = st.button("승인하고 다음으로", type="primary", use_container_width=True)
                    
                    if bottom_approve_clicked or top_approve_clicked:
                        
                        # 세션 상태에서 입력값 가져오기
                        color_input_key = f"edit_color_{current_index}"
                        current_edited_id = st.session_state.get(id_input_key, "")
                        current_edited_name = st.session_state.get(name_input_key, "")
                        current_edited_color = st.session_state.get(color_input_key, "")
                        
                        # 라인, 디테일, 소재 확인
                        selected_line = list(st.session_state[line_key])
                        selected_detail = list(st.session_state[detail_key])
                        selected_material = list(st.session_state[material_key])
                        
                        if not selected_line:
                            st.warning("라인을 1개 선택해주세요.")
                            st.stop()
                        
                        if not selected_material:
                            st.warning("소재를 1개 이상 선택해주세요.")
                            st.stop()
                        
                        # 현재까지 편집된 모든 레코드의 name과 id 확인
                        existing_names = set()
                        existing_ids = set()
                        for idx, record in enumerate(edit_records):
                            if idx < current_index:
                                schema = record.get("schema", {})
                                existing_name = schema.get("name", "")
                                existing_id = schema.get("id", "")
                                if existing_name:
                                    existing_names.add(existing_name)
                                if existing_id:
                                    existing_ids.add(existing_id)
                        
                        # name과 id 자동 생성
                        auto_name, auto_id = generate_dress_name_and_id(
                            selected_line,
                            selected_detail,
                            selected_material,
                            existing_names,
                            existing_ids,
                        )
                        
                        # 사용자가 수동으로 입력한 경우도 확인 (빈 값이면 자동 생성된 값 사용)
                        final_name = current_edited_name.strip() if current_edited_name.strip() else auto_name
                        final_id = current_edited_id.strip() if current_edited_id.strip() else auto_id
                        
                        # 원본 ID 저장 (중복 처리 전)
                        base_id = final_id
                        
                        # ID 중복 확인 및 넘버링 추가 (수동 입력한 경우도 처리)
                        if final_id in existing_ids:
                            counter = 1
                            while final_id in existing_ids:
                                final_id = f"{base_id}_{counter:02d}"
                                counter += 1
                        
                        # 현재 레코드 업데이트
                        updated_schema = {
                            "id": final_id,
                            "name": final_name,
                            "color": current_edited_color,
                            "line": selected_line,
                            "material": selected_material,
                            "neckline": list(st.session_state[neckline_key]),
                            "sleeve": list(st.session_state[sleeve_key]),
                            "keyword": list(st.session_state[keyword_key]),
                            "detail": selected_detail,
                            "dress_lengths": list(st.session_state[dress_lengths_key]),
                        }
                        
                        edit_records[current_index]["schema"] = updated_schema
                        st.session_state["edit_records"] = edit_records
                        
                        # 이미지 파일명 변경 (schema.id 기반)
                        current_record = edit_records[current_index]
                        old_file_path = current_record.get("file_path", "")
                        if old_file_path and Path(old_file_path).exists():
                            old_path = Path(old_file_path)
                            file_ext = old_path.suffix
                            new_image_name = final_id
                            new_file_name = f"{new_image_name}{file_ext}"
                            new_file_path = get_dress_images_dir() / new_file_name
                            
                            # 파일명 중복 처리
                            counter = 1
                            original_new_path = new_file_path
                            while new_file_path.exists() and new_file_path != old_path:
                                stem = original_new_path.stem
                                new_file_path = get_dress_images_dir() / f"{stem}_{counter:02d}{file_ext}"
                                counter += 1
                            
                            try:
                                # 파일명 변경
                                old_path.rename(new_file_path)
                                # 레코드 업데이트
                                current_record["image_name"] = new_file_path.stem
                                current_record["file_path"] = str(new_file_path)
                                edit_records[current_index] = current_record
                                st.session_state["edit_records"] = edit_records
                            except Exception as e:
                                st.warning(f"파일명 변경 실패: {e}")
                        
                        # 즉시 파일에 저장 (하단 표에 반영되도록)
                        overwrite_store(store_path, edit_records)
                        
                        # ID가 변경된 경우 알림
                        if final_id != base_id:
                            st.info(f"ID가 중복되어 자동으로 변경되었습니다: {base_id} → {final_id}")
                        
                        # 다음 이미지로 이동
                        st.session_state["edit_image_index"] = current_index + 1
                        
                        # 세션 상태 초기화 (다음 이미지 준비)
                        color_input_key = f"edit_color_{current_index}"
                        for key in [line_key, material_key, neckline_key, sleeve_key, keyword_key, detail_key, dress_lengths_key, id_input_key, name_input_key, color_input_key]:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()
            else:
                # 모든 이미지 처리 완료
                st.success("모든 이미지 편집이 완료되었습니다!")
                st.info("모든 편집 내용이 이미 저장되었습니다. 하단 '데이터 관리' 섹션에서 확인할 수 있습니다.")
                
                # 최종 데이터 저장 (이미 저장되어 있지만, 확실히 하기 위해 다시 저장)
                if st.button("데이터 저장", type="primary"):
                    overwrite_store(store_path, edit_records)
                    st.success("데이터가 저장되었습니다!")
                    st.session_state["edit_mode"] = False
                    st.session_state["edit_image_index"] = 0
                    st.session_state["edit_records"] = []
                    st.rerun()
                
                # 다운로드 버튼
                st.divider()
                st.subheader("다운로드")
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
                    # JSON 다운로드
                    payload = json.dumps(edit_records, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="JSON 다운로드",
                        data=payload.encode("utf-8"),
                        file_name=f"dress_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                
                with col_dl2:
                    # CSV 다운로드
                    csv_data = []
                    for r in edit_records:
                        schema = r.get("schema", {}) or {}
                        csv_row = {
                            "id": r.get("id"),
                            "created_at": r.get("created_at"),
                            "image_name": r.get("image_name"),
                            "original_name": r.get("original_name", ""),
                            "prompt": r.get("prompt"),
                            "name": schema.get("name"),
                            "line": json.dumps(schema.get("line", []), ensure_ascii=False, separators=(',', ':')),
                            "material": json.dumps(schema.get("material", []), ensure_ascii=False, separators=(',', ':')),
                            "color": schema.get("color"),
                            "neckline": json.dumps(schema.get("neckline", []), ensure_ascii=False, separators=(',', ':')),
                            "sleeve": json.dumps(schema.get("sleeve", []), ensure_ascii=False, separators=(',', ':')),
                            "keyword": json.dumps(schema.get("keyword", []), ensure_ascii=False, separators=(',', ':')),
                            "detail": json.dumps(schema.get("detail", []), ensure_ascii=False, separators=(',', ':')),
                            "dress_lengths": json.dumps(schema.get("dress_lengths", []), ensure_ascii=False, separators=(',', ':')),
                        }
                        csv_data.append(csv_row)
                    
                    csv_df = pd.DataFrame(csv_data)
                    csv_content = csv_df.to_csv(index=False, encoding='utf-8-sig')
                    
                    st.download_button(
                        label="CSV 다운로드 (Supabase용)",
                        data=csv_content.encode('utf-8-sig'),
                        file_name=f"dress_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                
                # 편집 모드 종료 버튼
                if st.button("편집 모드 종료", use_container_width=True):
                    st.session_state["edit_mode"] = False
                    st.session_state["edit_image_index"] = 0
                    st.session_state["edit_records"] = []
                    st.rerun()
        
        st.divider()
    
    st.subheader("데이터 관리")
    rows = load_store(store_path)
    if not rows:
        st.info("저장된 데이터가 없습니다. 이미지를 업로드하여 분석해 보세요.")
        return

    # 테이블 렌더링
    if view_mode == "플랫":
        flat_rows = [flatten_record(r) for r in rows]
        df = pd.DataFrame(flat_rows)
    elif view_mode == "CSV":
        # CSV 모드에서는 Supabase 업로드용 형식으로 변환
        csv_rows = []
        for r in rows:
            schema = r.get("schema", {}) or {}
            csv_row = {
                "id": r.get("id"),
                "created_at": r.get("created_at"),
                "image_name": r.get("image_name"),
                "original_name": r.get("original_name", ""),
                "prompt": r.get("prompt"),
                "name": schema.get("name"),
                "line": json.dumps(schema.get("line", []), ensure_ascii=False, separators=(',', ':')),
                "material": json.dumps(schema.get("material", []), ensure_ascii=False, separators=(',', ':')),
                "color": schema.get("color"),
                "neckline": json.dumps(schema.get("neckline", []), ensure_ascii=False, separators=(',', ':')),
                "sleeve": json.dumps(schema.get("sleeve", []), ensure_ascii=False, separators=(',', ':')),
                "keyword": json.dumps(schema.get("keyword", []), ensure_ascii=False, separators=(',', ':')),
                "detail": json.dumps(schema.get("detail", []), ensure_ascii=False, separators=(',', ':')),
                "dress_lengths": json.dumps(schema.get("dress_lengths", []), ensure_ascii=False, separators=(',', ':')),
            }
            csv_rows.append(csv_row)
        df = pd.DataFrame(csv_rows)
    else:
        # 원본 JSON 모드에서는 문자열로 표시
        df = pd.DataFrame(
            [
                {
                    "id": r.get("id"),
                    "created_at": r.get("created_at"),
                    "image_name": r.get("image_name"),
                    "json": json.dumps(r, ensure_ascii=False),
                }
                for r in rows
            ]
        )

    # 체크박스 선택을 위한 세션 상태 초기화
    if "selected_rows" not in st.session_state:
        st.session_state["selected_rows"] = set()
    
    # 데이터 표시
    st.subheader("데이터 표")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("데이터 선택 및 관리")
    
    # 전체 선택/해제 버튼
    col_select_all, col_clear_all = st.columns(2)
    with col_select_all:
        if st.button("전체 선택"):
            # 모든 행의 ID를 선택 상태로 설정
            all_ids = set(str(row.get("id")) for row in rows)
            st.session_state["selected_rows"] = all_ids
            # 체크박스 key들을 초기화하여 새로고침 시 반영되도록 함
            for row in rows:
                row_id = str(row.get("id"))
                checkbox_key = f"checkbox_{row_id}"
                if checkbox_key in st.session_state:
                    del st.session_state[checkbox_key]
            st.rerun()
    with col_clear_all:
        if st.button("전체 해제"):
            # 모든 선택 해제
            st.session_state["selected_rows"] = set()
            # 체크박스 key들을 초기화하여 새로고침 시 반영되도록 함
            for row in rows:
                row_id = str(row.get("id"))
                checkbox_key = f"checkbox_{row_id}"
                if checkbox_key in st.session_state:
                    del st.session_state[checkbox_key]
            st.rerun()
    
    # 각 행에 체크박스 추가 (간단한 리스트 형태)
    selected_ids = []
    for i, row in enumerate(rows):
        row_id = str(row.get("id"))
        is_selected = row_id in st.session_state["selected_rows"]
        
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            # 체크박스의 현재 상태 (세션 상태와 동기화)
            checkbox_key = f"checkbox_{row_id}"
            checkbox_is_checked = st.checkbox("선택", value=is_selected, key=checkbox_key, label_visibility="collapsed")
            
            # 체크박스 상태에 따라 세션 상태 업데이트
            if checkbox_is_checked:
                st.session_state["selected_rows"].add(row_id)
                selected_ids.append(row_id)
            else:
                st.session_state["selected_rows"].discard(row_id)
        
        with col2:
            if view_mode == "플랫":
                flat_row = flatten_record(row)
                st.write(f"**ID:** {flat_row.get('id')} | **파일:** {flat_row.get('image_name')} | **이름:** {flat_row.get('name')}")
            elif view_mode == "CSV":
                schema = row.get("schema", {}) or {}
                st.write(f"**ID:** {row.get('id')} | **파일:** {row.get('image_name')} | **이름:** {schema.get('name')}")
            else:
                st.write(f"**ID:** {row.get('id')} | **파일:** {row.get('image_name')}")
    
    st.markdown("---")
    st.subheader("선택된 데이터 작업")
    
    # 선택된 항목 표시
    if st.session_state["selected_rows"]:
        st.info(f"선택된 항목: {len(st.session_state['selected_rows'])}개")
        selected_ids_str = ",".join(st.session_state["selected_rows"])
    else:
        st.warning("선택된 항목이 없습니다.")
        selected_ids_str = ""
    
    # 기존 수동 입력 방식도 유지
    manual_ids = st.text_input(
        "또는 수동으로 id 입력 (쉼표로 구분)",
        value=selected_ids_str,
        help="체크박스 선택과 수동 입력을 함께 사용할 수 있습니다.",
    )

    def filter_rows_by_ids(all_rows: List[Dict[str, Any]], ids_text: str) -> List[Dict[str, Any]]:
        ids = [s.strip() for s in ids_text.split(",") if s.strip()] if ids_text else []
        if not ids:
            return all_rows
        id_set = set(ids)
        return [r for r in all_rows if str(r.get("id")) in id_set]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("클립보드로 복사 (플랫 텍스트)"):
            target_rows = filter_rows_by_ids(rows, manual_ids)
            if target_rows:
                flat_text = "\n\n".join(
                    [
                        (flatten_record(r).get("prompt") or "")
                        + "\n" + json.dumps(r.get("schema", {}), ensure_ascii=False)
                        for r in target_rows
                    ]
                )
                st.code(flat_text, language="text")
                st.info("위 블록을 복사하세요.")
            else:
                st.warning("선택된 항목이 없습니다.")

    with col2:
        if st.button("JSON 다운로드"):
            target_rows = filter_rows_by_ids(rows, manual_ids)
            if target_rows:
                payload = json.dumps(target_rows, ensure_ascii=False, indent=2)
                st.download_button(
                    label="다운로드 시작",
                    data=payload.encode("utf-8"),
                    file_name=f"dress_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )
            else:
                st.warning("선택된 항목이 없습니다.")

    with col3:
        if st.button("CSV 다운로드 (Supabase용)"):
            target_rows = filter_rows_by_ids(rows, manual_ids)
            if target_rows:
                # Supabase 업로드용 CSV 형식으로 변환
                csv_data = []
                for r in target_rows:
                    schema = r.get("schema", {}) or {}
                    csv_row = {
                        "id": r.get("id"),
                        "created_at": r.get("created_at"),
                        "image_name": r.get("image_name"),
                        "original_name": r.get("original_name", ""),
                        "prompt": r.get("prompt"),
                        "name": schema.get("name"),
                        "line": json.dumps(schema.get("line", []), ensure_ascii=False, separators=(',', ':')),
                        "material": json.dumps(schema.get("material", []), ensure_ascii=False, separators=(',', ':')),
                        "color": schema.get("color"),
                        "neckline": json.dumps(schema.get("neckline", []), ensure_ascii=False, separators=(',', ':')),
                        "sleeve": json.dumps(schema.get("sleeve", []), ensure_ascii=False, separators=(',', ':')),
                        "keyword": json.dumps(schema.get("keyword", []), ensure_ascii=False, separators=(',', ':')),
                        "detail": json.dumps(schema.get("detail", []), ensure_ascii=False, separators=(',', ':')),
                        "dress_lengths": json.dumps(schema.get("dress_lengths", []), ensure_ascii=False, separators=(',', ':')),
                    }
                    csv_data.append(csv_row)
                
                csv_df = pd.DataFrame(csv_data)
                csv_content = csv_df.to_csv(index=False, encoding='utf-8-sig')
                
                st.download_button(
                    label="CSV 다운로드",
                    data=csv_content.encode('utf-8-sig'),
                    file_name=f"dress_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("선택된 항목이 없습니다.")

    with col4:
        if st.button("선택 삭제", type="primary"):
            target_rows = filter_rows_by_ids(rows, manual_ids)
            if target_rows:
                target_ids = {str(r.get("id")) for r in target_rows}
                remaining = [r for r in rows if str(r.get("id")) not in target_ids]
                overwrite_store(store_path, remaining)
                # 선택 상태 초기화
                st.session_state["selected_rows"] = set()
                st.success(f"{len(target_rows)}개 항목이 삭제되었습니다. 페이지를 새로고침하거나 아래 '새로고침'을 눌러 반영하세요.")
            else:
                st.warning("삭제할 항목이 없습니다.")

    if st.button("새로고침"):
        st.rerun()


if __name__ == "__main__":
    main()


