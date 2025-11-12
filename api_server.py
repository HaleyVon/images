#!/usr/bin/env python3
"""
Virtual Try-On API Server
FastAPI 기반 Virtual Try-On API 서버
"""

import os
import tempfile
import base64
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from virtual_tryon import VirtualTryOn
from image_validator import ImageValidator

load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="Virtual Try-On API",
    description="Gemini를 활용한 Virtual Try-On API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 인스턴스
tryon_instance: Optional[VirtualTryOn] = None
validator_instance: Optional[ImageValidator] = None


def get_tryon():
    """VirtualTryOn 인스턴스 가져오기 (싱글톤)"""
    global tryon_instance
    if tryon_instance is None:
        tryon_instance = VirtualTryOn()
    return tryon_instance


def get_validator():
    """ImageValidator 인스턴스 가져오기 (싱글톤)"""
    global validator_instance
    if validator_instance is None:
        validator_instance = ImageValidator()
    return validator_instance


class ValidationResponse(BaseModel):
    """검증 응답 모델"""
    success: bool
    is_valid: bool
    data: dict
    error: Optional[str] = None


class TryOnResponse(BaseModel):
    """Try-On 응답 모델"""
    success: bool
    image_base64: Optional[str] = None
    mime_type: Optional[str] = None
    person: Optional[dict] = None
    clothing: Optional[dict] = None
    prompt: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Virtual Try-On API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "validate_person": "/validate/person",
            "validate_clothing": "/validate/clothing",
            "try_on": "/try-on",
            "try_on_wedding": "/try-on/wedding",
            "try_on_iterative": "/try-on/iterative"
        }
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


@app.post("/validate/person")
async def validate_person(
    image: UploadFile = File(...)
):
    """
    사람 이미지 검증

    Args:
        image: 업로드된 이미지 파일

    Returns:
        검증 결과
    """
    try:
        validator = get_validator()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(image.filename).suffix) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # 검증 수행
            result = validator.validate_person_image(tmp_path)

            return ValidationResponse(
                success=True,
                is_valid=result.is_person,
                data=result.model_dump()
            )

        finally:
            # 임시 파일 삭제
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        return ValidationResponse(
            success=False,
            is_valid=False,
            data={},
            error=str(e)
        )


@app.post("/validate/clothing")
async def validate_clothing(
    image: UploadFile = File(...)
):
    """
    의류 이미지 검증

    Args:
        image: 업로드된 이미지 파일

    Returns:
        검증 결과
    """
    try:
        validator = get_validator()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(image.filename).suffix) as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # 검증 수행
            result = validator.validate_clothing_image(tmp_path)

            return ValidationResponse(
                success=True,
                is_valid=result.is_clothing,
                data=result.model_dump()
            )

        finally:
            # 임시 파일 삭제
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        return ValidationResponse(
            success=False,
            is_valid=False,
            data={},
            error=str(e)
        )


@app.post("/try-on")
async def try_on(
    person_image: UploadFile = File(...),
    clothing_image: UploadFile = File(...),
    style: str = Form("default")
):
    """
    Virtual Try-On 수행

    Args:
        person_image: 사람 이미지
        clothing_image: 의류 이미지
        style: 스타일 (default, wedding)

    Returns:
        생성된 이미지
    """
    person_tmp_path = None
    clothing_tmp_path = None

    try:
        tryon = get_tryon()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(person_image.filename).suffix) as tmp:
            content = await person_image.read()
            tmp.write(content)
            person_tmp_path = Path(tmp.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(clothing_image.filename).suffix) as tmp:
            content = await clothing_image.read()
            tmp.write(content)
            clothing_tmp_path = Path(tmp.name)

        # Virtual Try-On 수행
        result = tryon.process_with_validation(
            str(person_tmp_path),
            str(clothing_tmp_path),
            style=style
        )

        if result["success"]:
            # 이미지를 base64로 인코딩
            image_data = result["image"]
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode("utf-8")
            else:
                image_base64 = image_data

            return TryOnResponse(
                success=True,
                image_base64=image_base64,
                mime_type=result.get("mime_type", "image/jpeg"),
                person=result.get("person"),
                clothing=result.get("clothing"),
                prompt=result.get("prompt")
            )
        else:
            return TryOnResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        return TryOnResponse(
            success=False,
            error=str(e)
        )

    finally:
        # 임시 파일 삭제
        if person_tmp_path:
            person_tmp_path.unlink(missing_ok=True)
        if clothing_tmp_path:
            clothing_tmp_path.unlink(missing_ok=True)


@app.post("/try-on/wedding")
async def try_on_wedding(
    person_image: UploadFile = File(...),
    clothing_image: UploadFile = File(...)
):
    """
    웨딩드레스 Virtual Try-On 수행

    Args:
        person_image: 신부 이미지
        clothing_image: 웨딩드레스 이미지

    Returns:
        생성된 이미지
    """
    return await try_on(person_image, clothing_image, style="wedding")


@app.post("/try-on/iterative")
async def try_on_iterative(
    person_image: UploadFile = File(...),
    clothing_image: UploadFile = File(...),
    iterations: int = Form(2)
):
    """
    반복 개선 모드 Virtual Try-On 수행

    Args:
        person_image: 사람 이미지
        clothing_image: 의류 이미지
        iterations: 반복 횟수

    Returns:
        생성된 이미지
    """
    person_tmp_path = None
    clothing_tmp_path = None

    try:
        tryon = get_tryon()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(person_image.filename).suffix) as tmp:
            content = await person_image.read()
            tmp.write(content)
            person_tmp_path = Path(tmp.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(clothing_image.filename).suffix) as tmp:
            content = await clothing_image.read()
            tmp.write(content)
            clothing_tmp_path = Path(tmp.name)

        # 반복 개선 모드 Virtual Try-On 수행
        result = tryon.iterative_try_on(
            str(person_tmp_path),
            str(clothing_tmp_path),
            iterations=iterations
        )

        if result["success"]:
            # 이미지를 base64로 인코딩
            image_data = result["image"]
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode("utf-8")
            else:
                image_base64 = image_data

            return TryOnResponse(
                success=True,
                image_base64=image_base64,
                mime_type=result.get("mime_type", "image/jpeg")
            )
        else:
            return TryOnResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        return TryOnResponse(
            success=False,
            error=str(e)
        )

    finally:
        # 임시 파일 삭제
        if person_tmp_path:
            person_tmp_path.unlink(missing_ok=True)
        if clothing_tmp_path:
            clothing_tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
