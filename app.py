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
            
            if auto_rename and result.get("schema", {}).get("name"):
                schema_name = result.get("schema", {}).get("name")
                # 파일 확장자 유지
                file_ext = Path(original_name).suffix
                new_name = f"{schema_name}{file_ext}"
                
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
                "image_name": final_path.name,  # 최종 파일명
                "original_name": original_name,  # 원본 파일명
                "file_path": str(final_path),  # 실제 파일 경로
                "prompt": result.get("prompt"),
                "schema": result.get("schema"),
            }
            append_store(store_path, record)
            st.session_state["_processed_names"].add(file.name)

        st.success("분석 및 저장이 완료되었습니다.")

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
                "line": schema.get("line", []),
                "material": schema.get("material", []),
                "color": schema.get("color"),
                "neckline": schema.get("neckline", []),
                "sleeve": schema.get("sleeve", []),
                "keyword": schema.get("keyword", []),
                "detail": schema.get("detail", []),
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
            st.session_state["selected_rows"] = set(str(row.get("id")) for row in rows)
    with col_clear_all:
        if st.button("전체 해제"):
            st.session_state["selected_rows"] = set()
    
    # 각 행에 체크박스 추가 (간단한 리스트 형태)
    selected_ids = []
    for i, row in enumerate(rows):
        row_id = str(row.get("id"))
        is_selected = row_id in st.session_state["selected_rows"]
        
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            if st.checkbox("", value=is_selected, key=f"checkbox_{row_id}"):
                if row_id not in st.session_state["selected_rows"]:
                    st.session_state["selected_rows"].add(row_id)
                selected_ids.append(row_id)
            else:
                if row_id in st.session_state["selected_rows"]:
                    st.session_state["selected_rows"].remove(row_id)
        
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
                        "line": json.dumps(schema.get("line", []), ensure_ascii=False),
                        "material": json.dumps(schema.get("material", []), ensure_ascii=False),
                        "color": schema.get("color"),
                        "neckline": json.dumps(schema.get("neckline", []), ensure_ascii=False),
                        "sleeve": json.dumps(schema.get("sleeve", []), ensure_ascii=False),
                        "keyword": json.dumps(schema.get("keyword", []), ensure_ascii=False),
                        "detail": json.dumps(schema.get("detail", []), ensure_ascii=False),
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


