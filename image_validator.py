#!/usr/bin/env python3
"""
Image Validator Module
이미지 검증 모듈: 사람 이미지와 의류 이미지를 검증합니다.
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv

load_dotenv()


class Person(BaseModel):
    """사람 이미지 분석 결과"""
    is_person: bool = Field(..., description="Whether the image contains a person")
    description: str = Field(..., description="Description of the person in the image")
    body_visible: bool = Field(default=True, description="Whether full body or upper body is visible")
    pose_suitable: bool = Field(default=True, description="Whether pose is suitable for try-on")


class ClothingItem(BaseModel):
    """의류 이미지 분석 결과"""
    is_clothing: bool = Field(..., description="Whether this image is a clothing item")
    clothing_type: str = Field(..., description="Type of clothing (e.g., dress, shirt, pants)")
    description: str = Field(..., description="Detailed description of the clothing")
    color: str = Field(default="", description="Primary color of the clothing")
    pattern: str = Field(default="", description="Pattern or texture description")


class ImageValidator:
    """이미지 검증 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Gemini API 키 (None일 경우 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다. "
                ".env 파일을 생성하거나 환경변수로 설정해주세요."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash-exp"

    def encode_image(self, image_path: Path) -> tuple[bytes, str]:
        """
        이미지를 base64로 인코딩

        Args:
            image_path: 이미지 파일 경로

        Returns:
            (image_data, media_type) 튜플
        """
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # 파일 확장자에 따라 media type 결정
        extension = image_path.suffix.lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(extension, "image/jpeg")

        return image_data, media_type

    def validate_person_image(self, image_path: Path) -> Person:
        """
        사람 이미지 검증

        Args:
            image_path: 사람 이미지 파일 경로

        Returns:
            Person 객체
        """
        if not image_path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 로드
        image_data, media_type = self.encode_image(image_path)

        prompt = """
Analyze this image and determine:
1. Does it contain a clearly visible person? (full body or upper body)
2. If yes, describe the person briefly (gender, approximate age, clothing worn, pose)
3. Is the person's body clearly visible (not obscured)?
4. Is the pose suitable for virtual try-on (standing, front-facing preferred)?

Return EXACTLY one JSON object (no markdown, no extra text):
{
    "is_person": true/false,
    "description": "brief description",
    "body_visible": true/false,
    "pose_suitable": true/false
}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    {"mime_type": media_type, "data": image_data}
                ]
            )

            # 응답 파싱
            response_text = response.text.strip()

            # JSON 추출 (마크다운 코드블록 제거)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)
            return Person(**data)

        except Exception as e:
            raise ValueError(f"사람 이미지 검증 실패: {e}")

    def validate_clothing_image(self, image_path: Path) -> ClothingItem:
        """
        의류 이미지 검증

        Args:
            image_path: 의류 이미지 파일 경로

        Returns:
            ClothingItem 객체
        """
        if not image_path.exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 로드
        image_data, media_type = self.encode_image(image_path)

        prompt = """
Analyze this image and determine:
1. Is this a clothing item (dress, shirt, pants, jacket, etc.)?
2. If yes, identify the specific type
3. Describe key details (color, pattern, style, material, design elements)
4. What is the primary color?
5. Are there any patterns or textures?

Return EXACTLY one JSON object (no markdown, no extra text):
{
    "is_clothing": true/false,
    "clothing_type": "type",
    "description": "detailed description",
    "color": "primary color",
    "pattern": "pattern or texture description"
}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    {"mime_type": media_type, "data": image_data}
                ]
            )

            # 응답 파싱
            response_text = response.text.strip()

            # JSON 추출 (마크다운 코드블록 제거)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)
            return ClothingItem(**data)

        except Exception as e:
            raise ValueError(f"의류 이미지 검증 실패: {e}")


def main():
    """테스트용 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="이미지 검증 도구")
    parser.add_argument("image_path", help="검증할 이미지 파일 경로")
    parser.add_argument("--type", choices=["person", "clothing"], required=True,
                        help="이미지 타입 (person 또는 clothing)")
    parser.add_argument("--api-key", help="Gemini API 키", default=None)

    args = parser.parse_args()

    try:
        validator = ImageValidator(api_key=args.api_key)
        image_path = Path(args.image_path)

        if args.type == "person":
            print(f"사람 이미지 검증 중: {image_path}")
            result = validator.validate_person_image(image_path)
            print("\n검증 결과:")
            print(f"  사람 포함: {result.is_person}")
            print(f"  설명: {result.description}")
            print(f"  신체 가시성: {result.body_visible}")
            print(f"  적합한 포즈: {result.pose_suitable}")
        else:
            print(f"의류 이미지 검증 중: {image_path}")
            result = validator.validate_clothing_image(image_path)
            print("\n검증 결과:")
            print(f"  의류 여부: {result.is_clothing}")
            print(f"  의류 타입: {result.clothing_type}")
            print(f"  설명: {result.description}")
            print(f"  색상: {result.color}")
            print(f"  패턴: {result.pattern}")

    except Exception as e:
        print(f"오류 발생: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
