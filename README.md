# 드레스 이미지 프롬프트 생성기 (Dress Image Prompt Generator)

드레스 이미지를 분석하여 상세한 이미지 프롬프트와 구조화된 스키마를 자동으로 생성하는 AI 기반 도구입니다.

## 기능

- 🎨 **이미지 분석**: Claude Vision API를 사용하여 드레스 이미지를 상세히 분석
- 📝 **프롬프트 생성**: 드레스를 재현할 수 있는 상세한 영문 설명 자동 생성
- 🏷️ **스키마 생성**: 드레스의 라인, 소재, 색상, 넥라인, 소매 등을 구조화된 태그로 분류
- 💾 **JSON 출력**: 결과를 JSON 형식으로 저장하여 데이터베이스나 다른 시스템과 쉽게 연동

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd images
```

### 2. Python 가상환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. API 키 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, Anthropic API 키를 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일을 열어서 API 키를 입력:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

API 키는 [Anthropic Console](https://console.anthropic.com/)에서 발급받을 수 있습니다.

## 사용 방법

### 기본 사용

```bash
python dress_prompt_generator.py <이미지_파일_경로>
```

예시:
```bash
python dress_prompt_generator.py A_high_beaded.png
```

결과는 `A_high_beaded_result.json` 파일로 저장됩니다.

### 출력 파일명 지정

```bash
python dress_prompt_generator.py A_high_beaded.png -o my_result.json
```

### 화면에 결과 출력

```bash
python dress_prompt_generator.py A_high_beaded.png --show
```

### 모든 옵션 사용

```bash
python dress_prompt_generator.py A_high_beaded.png -o output.json --show
```

## 출력 형식

프로그램은 다음과 같은 JSON 형식으로 결과를 생성합니다:

```json
{
  "prompt": "an elegant off-shoulder wedding gown made of ivory tulle and shimmering lace fabric. The dress features a sweetheart neckline with soft floral appliqué and layered off-shoulder sleeves, a structured corset bodice decorated with beaded embroidery, and a voluminous A-line skirt covered with delicate sequins and floral lace patterns.",
  "schema": {
    "name": "Aline_off-shoulder_tulle-lace_layered",
    "line": ["A-line"],
    "material": ["Tulle", "Lace"],
    "color": "Ivory",
    "neckline": ["Off-shoulder", "Sweetheart"],
    "sleeve": ["Off-shoulder"],
    "keyword": ["Elegant", "Romantic", "Floral"],
    "detail": ["Beaded embroidery", "Floral appliqué", "Sequins", "Corset bodice"]
  }
}
```

### 스키마 컬럼 설명

| 컬럼 | 설명 | 예시 |
|------|------|------|
| `name` | 드레스 이름 (라인_넥라인_소재_소매 형식) | `Mermaid_off-shoulder_silk_longsleeve` |
| `line` | 드레스 라인 태그 배열 | `["A-line"]`, `["Mermaid"]`, `["Ball gown"]` |
| `material` | 소재 태그 배열 | `["Lace", "Tulle"]`, `["Silk"]` |
| `color` | 색상 | `Ivory`, `White`, `Blush` |
| `neckline` | 넥라인 태그 배열 | `["Off-shoulder"]`, `["V-neck"]` |
| `sleeve` | 소매 태그 배열 | `["Long sleeve"]`, `["Sleeveless"]` |
| `keyword` | 키워드 태그 배열 | `["Romantic", "Vintage", "Modern"]` |
| `detail` | 디테일 태그 배열 | `["Beaded", "Embroidered", "Sequins"]` |

## 명령행 옵션

```
usage: dress_prompt_generator.py [-h] [-o OUTPUT] [--show] [--api-key API_KEY] image_path

positional arguments:
  image_path            분석할 드레스 이미지 파일 경로

optional arguments:
  -h, --help            도움말 표시
  -o OUTPUT, --output OUTPUT
                        결과를 저장할 JSON 파일 경로 (기본: 입력파일명_result.json)
  --show                결과를 화면에 출력
  --api-key API_KEY     Anthropic API 키 (환경변수 대신 사용)
```

## 예시 이미지

이 저장소에는 다음과 같은 샘플 드레스 이미지가 포함되어 있습니다:

- `A_high_beaded.png` - A라인, 하이 넥라인, 비즈 장식
- `A_off_puff_lace.png` - A라인, 오프숄더, 퍼프 소매, 레이스
- `mermaid_boat_white_dobi.png` - 머메이드 라인, 보트 넥라인
- `bell_sleeveless_tube_white_silk_lace.png` - 벨 라인, 민소매, 튜브탑

## 배치 처리 예시

여러 이미지를 한 번에 처리하려면 간단한 스크립트를 작성할 수 있습니다:

```bash
#!/bin/bash
for img in *.png; do
  echo "Processing $img..."
  python dress_prompt_generator.py "$img"
done
```

## 문제 해결

### API 키 오류

```
ValueError: ANTHROPIC_API_KEY가 설정되지 않았습니다.
```

- `.env` 파일이 존재하는지 확인
- `.env` 파일에 올바른 API 키가 입력되었는지 확인
- 또는 `--api-key` 옵션으로 직접 API 키 제공

### 이미지 파일 오류

```
FileNotFoundError: 이미지 파일을 찾을 수 없습니다
```

- 이미지 파일 경로가 올바른지 확인
- 지원되는 이미지 형식: PNG, JPG, JPEG, GIF, WEBP

## 기술 스택

- **Python 3.7+**
- **Anthropic Claude API** - 이미지 분석 및 텍스트 생성
- **python-dotenv** - 환경변수 관리

## 라이선스

MIT License

## 기여

이슈나 풀 리퀘스트는 언제든지 환영합니다!

## 문의

문제가 있거나 질문이 있으시면 이슈를 등록해 주세요.
