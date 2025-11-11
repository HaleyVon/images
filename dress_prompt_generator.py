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

    # 허용 어휘 목록 (시스템 검증용)
    ALLOWED_LINES = ["티렝스", "미니", "A라인", "엠파이어라인", "시스", "H라인", "머메이드", "벨라인", "볼가운", "프린세스라인"]
    ALLOWED_MATERIALS = ["비즈", "새틴", "미카도실크", "오간자", "레이스", "쉬폰", "튤(망사)", "도비실크", "크레이프", "타프타실크"]
    ALLOWED_NECKLINES = ["브이넥", "하트넥", "오프숄더", "하이넥", "보트넥", "스퀘어넥", "일루전 넥", "스트레이트 어크로스", "언밸런스", "홀터넥"]
    ALLOWED_SLEEVES = ["슬리브리스", "롱슬리브", "7부", "숏슬리브", "일루전슬리브", "비숍슬리브", "벨슬리브", "드레이프 슬리브", "퍼프슬리브"]
    ALLOWED_KEYWORDS = ["럭셔리", "드라마틱", "클래식", "우아한", "로맨틱", "빈티지", "모던", "미니멀", "귀여운", "볼륨", "포멀", "로얄", "시크", "도시적인"]
    ALLOWED_DETAILS = ["비즈", "시퀸", "긴 트레인", "드레이핑", "코르셋", "일루전 백", "아플리케 레이스", "리본", "러플", "레이어드 스커트", "플리츠"]
    ALLOWED_DRESS_LENGTHS = ["종아리 길이", "발목 길이", "스윕 트레인(바닥 닿는 길이)", "채플 트레인(뒤가 약간 끌림)", "캐시드럴 트레인(뒤가 길게 끌림)", "미니", "무릎 길이"]
    
    # 한국어 -> 영문 변환 맵 (ID 생성용)
    KOREAN_TO_ENGLISH = {
        # 라인
        "티렝스": "tiered",
        "미니": "mini",
        "A라인": "a-line",
        "엠파이어라인": "empire-line",
        "시스": "sheath",
        "H라인": "h-line",
        "머메이드": "mermaid",
        "벨라인": "ball-line",
        "볼가운": "ballgown",
        "프린세스라인": "princess-line",
        # 소재
        "비즈": "bead",
        "새틴": "satin",
        "미카도실크": "mikado-silk",
        "오간자": "organza",
        "레이스": "lace",
        "쉬폰": "chiffon",
        "튤(망사)": "tulle",
        "도비실크": "dobby-silk",
        "크레이프": "crepe",
        "타프타실크": "taffeta-silk",
        # 넥라인
        "브이넥": "v-neck",
        "하트넥": "heart-neck",
        "오프숄더": "off-shoulder",
        "하이넥": "high-neck",
        "보트넥": "boat-neck",
        "스퀘어넥": "square-neck",
        "일루전 넥": "illusion-neck",
        "스트레이트 어크로스": "straight-across",
        "언밸런스": "unbalance",
        "홀터넥": "halter-neck",
        # 소매
        "슬리브리스": "sleeveless",
        "롱슬리브": "long-sleeve",
        "7부": "three-quarter",
        "숏슬리브": "short-sleeve",
        "일루전슬리브": "illusion-sleeve",
        "비숍슬리브": "bishop-sleeve",
        "벨슬리브": "bell-sleeve",
        "드레이프 슬리브": "drape-sleeve",
        "퍼프슬리브": "puff-sleeve",
        # 키워드
        "럭셔리": "luxury",
        "드라마틱": "dramatic",
        "클래식": "classic",
        "우아한": "elegant",
        "로맨틱": "romantic",
        "빈티지": "vintage",
        "모던": "modern",
        "미니멀": "minimal",
        "귀여운": "cute",
        "볼륨": "volume",
        "포멀": "formal",
        "로얄": "royal",
        "시크": "chic",
        "도시적인": "urban",
        # 디테일
        "시퀸": "sequin",
        "긴 트레인": "long-train",
        "드레이핑": "draping",
        "코르셋": "corset",
        "일루전 백": "illusion-back",
        "아플리케 레이스": "applique-lace",
        "리본": "ribbon",
        "러플": "ruffle",
        "레이어드 스커트": "layered-skirt",
        "플리츠": "pleats",
        # 드레스 길이
        "종아리 길이": "calf-length",
        "발목 길이": "ankle-length",
        "스윕 트레인(바닥 닿는 길이)": "sweep-train",
        "채플 트레인(뒤가 약간 끌림)": "chapel-train",
        "캐시드럴 트레인(뒤가 길게 끌림)": "cathedral-train",
        "무릎 길이": "knee-length",
    }

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
        # 모델명을 환경변수로 설정 가능하게 하고, 기본값을 Claude Haiku 4.5로 지정
        # 참고: 환경변수 ANTHROPIC_MODEL이 설정되어 있으면 이를 우선 사용합니다.
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

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

    def validate_schema(self, schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        스키마가 규칙에 맞는지 검증

        Args:
            schema: 검증할 스키마 딕셔너리

        Returns:
            (is_valid, errors) 튜플 - is_valid는 규칙 준수 여부, errors는 오류 메시지 리스트
        """
        import re
        errors: List[str] = []

        # id 검증: 영문 언더스코어 형식 (알파벳, 숫자, 언더스코어, 하이픈만 허용)
        schema_id = schema.get("id", "")
        if not schema_id:
            errors.append("id 필드가 없습니다.")
        elif not isinstance(schema_id, str):
            errors.append(f"id는 문자열이어야 합니다. 현재: {type(schema_id)}")
        else:
            if not re.match(r'^[a-zA-Z0-9_-]+$', schema_id):
                errors.append(f"id는 영문, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다. 현재: {schema_id}")

        # name 검증: "라인_디테일(있을경우)_소재 드레스" 형식
        name = schema.get("name", "")
        if not name:
            errors.append("name 필드가 없습니다.")
        elif not isinstance(name, str):
            errors.append(f"name은 문자열이어야 합니다. 현재: {type(name)}")
        else:
            if not name.endswith(" 드레스"):
                errors.append(f"name은 ' 드레스'로 끝나야 합니다. 현재: {name}")
            # 언더스코어로 구분되어 있는지 확인 (최소 2개: 라인_소재, 최대 3개: 라인_디테일_소재)
            parts = name.replace(" 드레스", "").split("_")
            if len(parts) < 2 or len(parts) > 3:
                errors.append(f"name은 '라인_소재 드레스' 또는 '라인_디테일_소재 드레스' 형식이어야 합니다. 현재: {name}")

        # color 검증: 문자열이고 비어있지 않아야 함
        color = schema.get("color", "")
        if not isinstance(color, str):
            errors.append(f"color는 문자열이어야 합니다. 현재: {type(color)}")
        elif not color:
            errors.append("color는 비어있을 수 없습니다.")

        # 배열 필드 검증: 허용 어휘 목록에 있는지 확인
        array_fields = {
            "line": (schema.get("line", []), self.ALLOWED_LINES),
            "material": (schema.get("material", []), self.ALLOWED_MATERIALS),
            "neckline": (schema.get("neckline", []), self.ALLOWED_NECKLINES),
            "sleeve": (schema.get("sleeve", []), self.ALLOWED_SLEEVES),
            "keyword": (schema.get("keyword", []), self.ALLOWED_KEYWORDS),
            "detail": (schema.get("detail", []), self.ALLOWED_DETAILS),
            "dress_lengths": (schema.get("dress_lengths", []), self.ALLOWED_DRESS_LENGTHS),
        }

        for field_name, (values, allowed_list) in array_fields.items():
            if not isinstance(values, list):
                errors.append(f"{field_name}는 리스트여야 합니다. 현재: {type(values)}")
                continue
            
            for value in values:
                if not isinstance(value, str):
                    errors.append(f"{field_name}의 값은 모두 문자열이어야 합니다. 현재: {value} ({type(value)})")
                elif value not in allowed_list:
                    errors.append(f"{field_name}의 '{value}'는 허용 어휘 목록에 없습니다. 허용 목록: {allowed_list}")
        
        # 개수 제한 검증
        dress_lengths = schema.get("dress_lengths", [])
        if isinstance(dress_lengths, list):
            if len(dress_lengths) != 1:
                errors.append(f"dress_lengths는 정확히 1개만 선택해야 합니다. 현재: {len(dress_lengths)}개")
        
        keyword = schema.get("keyword", [])
        if isinstance(keyword, list):
            if len(keyword) < 1 or len(keyword) > 3:
                errors.append(f"keyword는 1~3개만 선택해야 합니다. 현재: {len(keyword)}개")

        return len(errors) == 0, errors

    def normalize_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        스키마를 규칙에 맞게 정규화 (자동 수정)

        Args:
            schema: 정규화할 스키마 딕셔너리

        Returns:
            정규화된 스키마 딕셔너리
        """
        import re
        normalized = schema.copy()

        # id 형식 정규화: 공백을 언더스코어로, 소문자로 변환, 특수문자 제거
        if normalized.get("id"):
            normalized["id"] = re.sub(r'[^a-zA-Z0-9_-]', '_', normalized["id"]).lower()
        
        # name 형식 정규화: 끝에 " 드레스" 추가 (없는 경우)
        # 주의: name은 자동 생성 함수에서 생성되므로 여기서는 형식만 확인
        if normalized.get("name") and not normalized["name"].endswith(" 드레스"):
            normalized["name"] = normalized["name"] + " 드레스"

        # 배열 필드에서 허용되지 않은 값 제거
        array_fields = {
            "line": self.ALLOWED_LINES,
            "material": self.ALLOWED_MATERIALS,
            "neckline": self.ALLOWED_NECKLINES,
            "sleeve": self.ALLOWED_SLEEVES,
            "keyword": self.ALLOWED_KEYWORDS,
            "detail": self.ALLOWED_DETAILS,
            "dress_lengths": self.ALLOWED_DRESS_LENGTHS,
        }

        for field_name, allowed_list in array_fields.items():
            if field_name in normalized and isinstance(normalized[field_name], list):
                normalized[field_name] = [v for v in normalized[field_name] if v in allowed_list]
        
        # 개수 제한 적용
        # dress_lengths: 정확히 1개만 허용
        if "dress_lengths" in normalized and isinstance(normalized["dress_lengths"], list):
            if len(normalized["dress_lengths"]) > 1:
                print(f"경고: dress_lengths는 1개만 선택 가능합니다. {len(normalized['dress_lengths'])}개 중 가장 근접한 한 개만 유지합니다.")
                normalized["dress_lengths"] = [normalized["dress_lengths"][0]]
            elif len(normalized["dress_lengths"]) == 0:
                print(f"경고: dress_lengths가 비어있습니다. 기본값 '발목 길이'를 설정합니다.")
                normalized["dress_lengths"] = ["발목 길이"]
        
        # keyword: 1~3개만 허용
        if "keyword" in normalized and isinstance(normalized["keyword"], list):
            if len(normalized["keyword"]) > 3:
                print(f"경고: keyword는 최대 3개까지만 선택 가능합니다. {len(normalized['keyword'])}개 중 가장 근접한 세 개만 유지합니다.")
                normalized["keyword"] = normalized["keyword"][:3]
            elif len(normalized["keyword"]) == 0:
                print(f"경고: keyword가 비어있습니다. 기본값 '우아한'을 설정합니다.")
                normalized["keyword"] = ["우아한"]

        return normalized

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
        prompt = """이 드레스 이미지를 상세히 분석하여 다음을 생성해주세요:

스키마: 아래 JSON 구조에 맞춰 한국어 태그만 사용해 작성하세요.
   - 중요 규칙 (반드시 지켜야 함):
     - id: name과 동일한 규칙으로 영문으로 작성하세요. 파일명으로 사용되므로 공백은 언더스코어(_)로, 특수문자는 피하세요.
       name이 "A라인_비즈_새틴 드레스"이면 id는 "a-line_bead_satin" 형식입니다.
       예시: "a-line_bead_satin", "sheath_satin"
     - 아래 제공된 허용 어휘 목록에서만 선택해 정확히 같은 단어와 띄어쓰기를 사용하세요.
     - 허용 목록에 없는 단어, 변형, 동의어, 영어 사용 금지 (id 제외).
     - 배열 항목 순서는 중요하지 않으나, 의미 중복은 피하세요.
     - color는 한국어 단일 문자열로 작성하세요. 예: "화이트", "아이보리", "블러쉬".
     - name 형식은 반드시 "라인_소재 드레스" 또는 "라인_디테일_소재 드레스"로 작성하세요.
       디테일이 있을 경우 대표적인 디테일 1개만 사용하세요.
       예시: "A라인_비즈_새틴 드레스", "시스_새틴 드레스"
     - **개수 제한 (매우 중요)**:
       * dress_lengths: 정확히 1개만 선택
       * keyword: 1~3개만 선택 (최대 3개)

허용 어휘:
- lines: ["티렝스", "미니", "A라인", "엠파이어라인", "시스", "H라인", "머메이드", "벨라인", "볼가운", "프린세스라인"]
- materials: ["비즈", "새틴", "미카도실크", "오간자", "레이스", "쉬폰", "튤(망사)", "도비실크", "크레이프", "타프타실크"]
- necklines: ["브이넥", "하트넥", "오프숄더", "하이넥", "보트넥", "스퀘어넥", "일루전 넥", "스트레이트 어크로스", "언밸런스", "홀터넥"]
- sleeves: ["슬리브리스", "롱슬리브", "7부", "숏슬리브", "일루전슬리브", "비숍슬리브", "벨슬리브", "드레이프 슬리브", "퍼프슬리브"]
- keywords: ["럭셔리", "드라마틱", "클래식", "우아한", "로맨틱", "빈티지", "모던", "미니멀", "귀여운", "볼륨", "포멀", "로얄", "시크", "도시적인"]
- details: ["비즈", "시퀸", "긴 트레인", "드레이핑", "코르셋", "일루전 백", "아플리케 레이스", "리본", "러플", "레이어드 스커트", "플리츠"]
- dress_lengths: ["종아리 길이", "발목 길이", "스윕 트레인(바닥 닿는 길이)", "채플 트레인(뒤가 약간 끌림)", "캐시드럴 트레인(뒤가 길게 끌림)", "미니", "무릎 길이"]

응답은 반드시 아래 JSON 형식으로만 출력하세요(설명 금지):
{
  "prompt": "",
  "schema": {
    "id": "sheath_v-neck_3quarter_crepe",
    "name": "A라인_비즈_새틴 드레스",
    "line": ["허용된 lines 값들"],
    "material": ["허용된 materials 값들"],
    "color": "화이트",
    "neckline": ["허용된 necklines 값들"],
    "sleeve": ["허용된 sleeves 값들"],
    "keyword": ["허용된 keywords 값들"],
    "detail": ["허용된 details 값들"],
    "dress_lengths": ["허용된 dress_lengths 값들"]
  }
}
"""

        message = self.client.messages.create(
            model=self.model,
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
            
            # 프롬프트 생성 로직은 당분간 사용하지 않음 (주석처리)
            # prompt가 없으면 빈 문자열로 설정
            if "prompt" not in result:
                result["prompt"] = ""
            
            # 스키마 검증 및 정규화
            schema = result.get("schema", {})
            if schema:
                # 먼저 정규화 수행
                result["schema"] = self.normalize_schema(schema)
                
                # 검증 수행
                is_valid, errors = self.validate_schema(result["schema"])
                if not is_valid:
                    error_msg = "스키마 검증 실패:\n" + "\n".join(f"  - {e}" for e in errors)
                    print(f"경고: {error_msg}")
                    print(f"정규화된 스키마: {json.dumps(result['schema'], ensure_ascii=False, indent=2)}")
                    # 검증 실패해도 정규화된 결과는 반환 (경고만 출력)
            
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
