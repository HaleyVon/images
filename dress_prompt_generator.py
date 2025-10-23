#!/usr/bin/env python3
"""
Dress Image Prompt Generator
드레스 이미지를 분석하여 상세한 프롬프트와 구조화된 스키마를 생성합니다.
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Dict, List, Any
import anthropic
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()


class DressPromptGenerator:
    """드레스 이미지 분석 및 프롬프트 생성 클래스"""

    def __init__(self, api_key: str = None):
        """
        초기화

        Args:
            api_key: Anthropic API 키 (None일 경우 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다. "
                ".env 파일을 생성하거나 환경변수로 설정해주세요."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def encode_image(self, image_path: str) -> tuple[str, str]:
        """
        이미지를 base64로 인코딩

        Args:
            image_path: 이미지 파일 경로

        Returns:
            (base64_encoded_data, media_type) 튜플
        """
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # 파일 확장자에 따라 media type 결정
        extension = Path(image_path).suffix.lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = media_type_map.get(extension, "image/png")

        return image_data, media_type

    def analyze_dress_image(self, image_path: str) -> Dict[str, Any]:
        """
        드레스 이미지를 분석하여 프롬프트와 스키마 생성

        Args:
            image_path: 드레스 이미지 파일 경로

        Returns:
            프롬프트와 스키마가 포함된 딕셔너리
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 인코딩
        image_data, media_type = self.encode_image(image_path)

        # Claude API를 사용하여 이미지 분석
        prompt = """이 드레스 이미지를 상세히 분석하여 다음 두 가지를 생성해주세요:

1. **이미지 프롬프트**: 드레스를 재현할 수 있는 상세한 영문 설명
   - 소재, 색상, 실루엣, 넥라인, 소매, 장식 등을 포함
   - 예시: "an elegant off-shoulder wedding gown made of ivory tulle and shimmering lace fabric. The dress features a sweetheart neckline with soft floral appliqué and layered off-shoulder sleeves, a structured corset bodice decorated with beaded embroidery, and a voluminous A-line skirt covered with delicate sequins and floral lace patterns."

2. **스키마**: 아래 구조에 맞춰 JSON 형식으로 작성
   - name: 드레스 이름 (예: "Mermaid_off-shoulder_silk_longsleeve") - 라인_넥라인_소재_소매 형식
   - line: 드레스 라인 태그 배열 (예: ["A-line"], ["Mermaid"], ["Ball gown"], ["Sheath"])
   - material: 소재 태그 배열 (예: ["Lace", "Tulle"], ["Silk"], ["Satin", "Organza"])
   - color: 색상 (예: "Ivory", "White", "Blush")
   - neckline: 넥라인 태그 배열 (예: ["Off-shoulder"], ["Sweetheart"], ["V-neck"], ["High neck"])
   - sleeve: 소매 태그 배열 (예: ["Long sleeve"], ["Sleeveless"], ["Cap sleeve"], ["Puff sleeve"])
   - keyword: 키워드 태그 배열 (예: ["Romantic", "Vintage", "Modern", "Elegant"])
   - detail: 디테일 태그 배열 (예: ["Beaded", "Embroidered", "Floral appliqué", "Sequins"])

응답은 반드시 아래 JSON 형식으로 해주세요:
{
  "prompt": "상세한 영문 프롬프트...",
  "schema": {
    "name": "드레스_이름",
    "line": ["라인"],
    "material": ["소재1", "소재2"],
    "color": "색상",
    "neckline": ["넥라인"],
    "sleeve": ["소매"],
    "keyword": ["키워드1", "키워드2"],
    "detail": ["디테일1", "디테일2"]
  }
}

JSON 형식만 출력하고, 다른 설명은 포함하지 마세요."""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # 응답 파싱
        response_text = message.content[0].text

        # JSON 추출 (마크다운 코드블록이 있을 수 있으므로)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            print(f"원본 응답:\n{response_text}")
            raise

    def save_result(self, result: Dict[str, Any], output_path: str):
        """
        결과를 JSON 파일로 저장

        Args:
            result: 분석 결과
            output_path: 출력 파일 경로
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✓ 결과가 저장되었습니다: {output_path}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="드레스 이미지를 분석하여 프롬프트와 스키마를 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python dress_prompt_generator.py input.png
  python dress_prompt_generator.py input.png -o output.json
  python dress_prompt_generator.py input.png --show
        """
    )

    parser.add_argument(
        "image_path",
        help="분석할 드레스 이미지 파일 경로"
    )

    parser.add_argument(
        "-o", "--output",
        help="결과를 저장할 JSON 파일 경로 (기본: 입력파일명_result.json)",
        default=None
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="결과를 화면에 출력"
    )

    parser.add_argument(
        "--api-key",
        help="Anthropic API 키 (환경변수 대신 사용)",
        default=None
    )

    args = parser.parse_args()

    try:
        # 생성기 초기화
        generator = DressPromptGenerator(api_key=args.api_key)

        # 이미지 분석
        print(f"이미지 분석 중: {args.image_path}")
        result = generator.analyze_dress_image(args.image_path)

        # 결과 출력
        if args.show:
            print("\n" + "="*80)
            print("IMAGE PROMPT:")
            print("="*80)
            print(result.get("prompt", ""))
            print("\n" + "="*80)
            print("SCHEMA:")
            print("="*80)
            print(json.dumps(result.get("schema", {}), ensure_ascii=False, indent=2))
            print("="*80 + "\n")

        # 결과 저장
        if args.output is None:
            # 기본 출력 파일명 생성
            input_path = Path(args.image_path)
            output_path = input_path.parent / f"{input_path.stem}_result.json"
        else:
            output_path = Path(args.output)

        generator.save_result(result, str(output_path))

        print(f"\n✓ 완료! 프롬프트와 스키마가 생성되었습니다.")

    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
