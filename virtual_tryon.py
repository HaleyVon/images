#!/usr/bin/env python3
"""
Virtual Try-On Module
Gemini API를 사용한 Virtual Try-On 구현
"""

import os
import io
import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image
from dotenv import load_dotenv

from image_validator import ImageValidator, Person, ClothingItem
from prompt_generator import PromptGenerator

load_dotenv()


class VirtualTryOn:
    """Virtual Try-On 클래스"""

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
        self.validator = ImageValidator(api_key=self.api_key)
        self.prompt_generator = PromptGenerator()

    def resize_image_for_api(
        self,
        image_path: Path,
        max_size: int = 1024
    ) -> bytes:
        """
        API 호출을 위한 이미지 리사이즈 (비용 최적화)

        Args:
            image_path: 이미지 파일 경로
            max_size: 최대 크기 (픽셀)

        Returns:
            리사이즈된 이미지 데이터 (bytes)
        """
        img = Image.open(image_path)

        # 이미 충분히 작으면 원본 반환
        if max(img.size) <= max_size:
            with open(image_path, "rb") as f:
                return f.read()

        # 비율 유지하며 리사이즈
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # JPEG로 변환 및 최적화
        output = io.BytesIO()
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        img.save(output, format="JPEG", quality=85, optimize=True)

        return output.getvalue()

    def generate_try_on_image(
        self,
        person_image_path: str,
        clothing_image_path: str,
        prompt: str,
        config: Optional[GenerateContentConfig] = None
    ) -> Dict[str, Any]:
        """
        Virtual Try-On 이미지 생성

        Args:
            person_image_path: 사람 이미지 경로
            clothing_image_path: 의류 이미지 경로
            prompt: 생성 프롬프트
            config: Gemini API 설정 (optional)

        Returns:
            생성 결과 딕셔너리
        """
        # 이미지 로드 및 리사이즈
        person_data = self.resize_image_for_api(Path(person_image_path))
        clothing_data = self.resize_image_for_api(Path(clothing_image_path))

        # 기본 설정
        if config is None:
            config = GenerateContentConfig(
                temperature=0.1,  # 낮은 temperature로 일관성 확보
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_modalities=["IMAGE"]  # 이미지 생성
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    {"mime_type": "image/jpeg", "data": person_data},
                    {"mime_type": "image/jpeg", "data": clothing_data}
                ],
                config=config
            )

            # 결과 추출
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            mime_type = part.inline_data.mime_type

                            return {
                                "success": True,
                                "image": image_data,
                                "mime_type": mime_type,
                                "description": ""
                            }

            return {
                "success": False,
                "error": "이미지를 생성하지 못했습니다."
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def safe_generate_with_retry(
        self,
        person_image_path: str,
        clothing_image_path: str,
        prompt: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        실패 시 자동 재시도

        Args:
            person_image_path: 사람 이미지 경로
            clothing_image_path: 의류 이미지 경로
            prompt: 생성 프롬프트
            max_retries: 최대 재시도 횟수

        Returns:
            생성 결과 딕셔너리
        """
        for attempt in range(max_retries):
            try:
                result = self.generate_try_on_image(
                    person_image_path,
                    clothing_image_path,
                    prompt
                )

                if result["success"]:
                    return result
                else:
                    print(f"시도 {attempt + 1}/{max_retries} 실패: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"시도 {attempt + 1}/{max_retries} 예외 발생: {e}")

                if attempt == max_retries - 1:
                    return {"success": False, "error": str(e)}

                # Exponential backoff
                time.sleep(2 ** attempt)

        return {"success": False, "error": "최대 재시도 횟수를 초과했습니다."}

    def iterative_try_on(
        self,
        person_image_path: str,
        clothing_image_path: str,
        iterations: int = 2
    ) -> Dict[str, Any]:
        """
        대화형 방식으로 품질 개선 (iterative refinement)

        Args:
            person_image_path: 사람 이미지 경로
            clothing_image_path: 의류 이미지 경로
            iterations: 반복 횟수

        Returns:
            최종 생성 결과 딕셔너리
        """
        # 초기 검증
        person_path = Path(person_image_path)
        clothing_path = Path(clothing_image_path)

        person = self.validator.validate_person_image(person_path)
        clothing = self.validator.validate_clothing_image(clothing_path)

        if not person.is_person:
            return {
                "success": False,
                "error": "사람 이미지가 아닙니다."
            }

        if not clothing.is_clothing:
            return {
                "success": False,
                "error": "의류 이미지가 아닙니다."
            }

        results = []

        for i in range(iterations):
            if i == 0:
                # 첫 번째 시도: 기본 프롬프트
                prompt = self.prompt_generator.generate_try_on_prompt(person, clothing)
            else:
                # 이후 시도: 개선 프롬프트
                prompt = f"""
Based on the previous attempt, improve the image by:
- Enhancing clothing texture details
- Adjusting fit to look more natural
- Ensuring perfect color matching
- Improving fabric draping
Generate an improved version.

Original requirements:
{self.prompt_generator.generate_try_on_prompt(person, clothing)}
"""

            print(f"\n반복 {i + 1}/{iterations}: 이미지 생성 중...")
            result = self.safe_generate_with_retry(
                person_image_path,
                clothing_image_path,
                prompt,
                max_retries=2
            )

            results.append(result)

            if not result["success"]:
                print(f"반복 {i + 1} 실패: {result.get('error')}")
                break

            print(f"반복 {i + 1} 완료!")

        # 최종 결과 반환 (마지막 성공한 결과)
        for result in reversed(results):
            if result.get("success"):
                return result

        return {"success": False, "error": "모든 시도가 실패했습니다."}

    def process_with_validation(
        self,
        person_image_path: str,
        clothing_image_path: str,
        style: str = "default"
    ) -> Dict[str, Any]:
        """
        검증 후 Virtual Try-On 수행 (전체 파이프라인)

        Args:
            person_image_path: 사람 이미지 경로
            clothing_image_path: 의류 이미지 경로
            style: 스타일 (default, wedding)

        Returns:
            생성 결과 딕셔너리
        """
        print("1단계: 이미지 검증 중...")

        person_path = Path(person_image_path)
        clothing_path = Path(clothing_image_path)

        # 검증
        try:
            person = self.validator.validate_person_image(person_path)
            clothing = self.validator.validate_clothing_image(clothing_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"이미지 검증 실패: {e}"
            }

        # 검증 결과 확인
        if not person.is_person:
            return {
                "success": False,
                "error": "사람 이미지가 아닙니다.",
                "person": person.model_dump()
            }

        if not clothing.is_clothing:
            return {
                "success": False,
                "error": "의류 이미지가 아닙니다.",
                "clothing": clothing.model_dump()
            }

        print(f"  ✓ 사람: {person.description}")
        print(f"  ✓ 의류: {clothing.clothing_type} - {clothing.description}")

        # 프롬프트 생성
        print("\n2단계: 프롬프트 생성 중...")
        if style == "wedding":
            prompt = self.prompt_generator.generate_wedding_dress_prompt(person, clothing)
        else:
            prompt = self.prompt_generator.generate_try_on_prompt(person, clothing)

        print("  ✓ 프롬프트 생성 완료")

        # 이미지 생성
        print("\n3단계: Virtual Try-On 이미지 생성 중...")
        result = self.safe_generate_with_retry(
            person_image_path,
            clothing_image_path,
            prompt,
            max_retries=3
        )

        if result["success"]:
            print("  ✓ 이미지 생성 완료!")
            result["person"] = person.model_dump()
            result["clothing"] = clothing.model_dump()
            result["prompt"] = prompt
        else:
            print(f"  ✗ 이미지 생성 실패: {result.get('error')}")

        return result


def main():
    """테스트용 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Virtual Try-On 도구")
    parser.add_argument("person_image", help="사람 이미지 경로")
    parser.add_argument("clothing_image", help="의류 이미지 경로")
    parser.add_argument("--output", "-o", help="출력 파일 경로", default="output.jpg")
    parser.add_argument("--style", choices=["default", "wedding"], default="default",
                        help="스타일 선택")
    parser.add_argument("--iterative", action="store_true",
                        help="반복 개선 모드 사용")
    parser.add_argument("--iterations", type=int, default=2,
                        help="반복 횟수 (iterative 모드)")
    parser.add_argument("--api-key", help="Gemini API 키", default=None)

    args = parser.parse_args()

    try:
        tryon = VirtualTryOn(api_key=args.api_key)

        if args.iterative:
            print(f"반복 개선 모드로 실행 (반복 {args.iterations}회)")
            result = tryon.iterative_try_on(
                args.person_image,
                args.clothing_image,
                iterations=args.iterations
            )
        else:
            result = tryon.process_with_validation(
                args.person_image,
                args.clothing_image,
                style=args.style
            )

        if result["success"]:
            # 이미지 저장
            output_path = Path(args.output)
            image_data = result["image"]

            # bytes인 경우 그대로 저장
            if isinstance(image_data, bytes):
                with open(output_path, "wb") as f:
                    f.write(image_data)
            else:
                # base64 디코딩이 필요한 경우
                image_bytes = base64.b64decode(image_data)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)

            print(f"\n✓ 성공! 결과가 저장되었습니다: {output_path}")
        else:
            print(f"\n✗ 실패: {result.get('error')}")
            return 1

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
