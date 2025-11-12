# 웨딩드레스 AI 시스템 (Wedding Dress AI System)

드레스 이미지를 분석하고 Virtual Try-On 기능을 제공하는 AI 기반 통합 시스템입니다.

## 주요 기능

### 1. 드레스 이미지 분석
- 🎨 **이미지 분석**: Claude Vision API를 사용하여 드레스 이미지를 상세히 분석
- 📝 **프롬프트 생성**: 드레스를 재현할 수 있는 상세한 영문 설명 자동 생성
- 🏷️ **스키마 생성**: 드레스의 라인, 소재, 색상, 넥라인, 소매 등을 구조화된 태그로 분류
- 💾 **JSON 출력**: 결과를 JSON 형식으로 저장하여 데이터베이스와 쉽게 연동

### 2. Virtual Try-On (NEW!)
- 👗 **가상 피팅**: Gemini API를 사용하여 실시간 가상 피팅 기능 제공
- 💒 **웨딩드레스 특화**: 웨딩드레스에 최적화된 고품질 가상 피팅
- 🔄 **반복 개선**: Iterative refinement로 품질 향상
- 🎯 **이미지 검증**: 자동으로 사람 이미지와 의류 이미지 검증
- 🚀 **REST API**: FastAPI 기반 RESTful API 제공

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

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, API 키를 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일을 열어서 API 키를 입력:

```
# 드레스 분석용
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Virtual Try-On용
GEMINI_API_KEY=your_gemini_api_key_here

# API 서버 포트
PORT=8000
```

API 키 발급:
- Anthropic API 키: [Anthropic Console](https://console.anthropic.com/)
- Gemini API 키: [Google AI Studio](https://aistudio.google.com/app/apikey)

## 사용 방법

### A. 드레스 이미지 분석

#### 기본 사용

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

### B. Virtual Try-On

#### CLI 사용

기본 사용법:
```bash
python virtual_tryon.py <사람_이미지> <의류_이미지> -o <출력_파일>
```

예시:
```bash
# 기본 모드
python virtual_tryon.py bride.jpg wedding_dress.jpg -o result.jpg

# 웨딩드레스 모드 (고품질)
python virtual_tryon.py bride.jpg wedding_dress.jpg -o result.jpg --style wedding

# 반복 개선 모드 (최고 품질)
python virtual_tryon.py bride.jpg wedding_dress.jpg -o result.jpg --iterative --iterations 3
```

#### API 서버 실행

```bash
# 서버 시작
python api_server.py

# 또는 uvicorn 직접 실행
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### API 엔드포인트

##### 1. 사람 이미지 검증
```bash
curl -X POST "http://localhost:8000/validate/person" \
  -F "image=@bride.jpg"
```

응답:
```json
{
  "success": true,
  "is_valid": true,
  "data": {
    "is_person": true,
    "description": "young woman, standing, front-facing",
    "body_visible": true,
    "pose_suitable": true
  }
}
```

##### 2. 의류 이미지 검증
```bash
curl -X POST "http://localhost:8000/validate/clothing" \
  -F "image=@dress.jpg"
```

응답:
```json
{
  "success": true,
  "is_valid": true,
  "data": {
    "is_clothing": true,
    "clothing_type": "wedding dress",
    "description": "elegant white A-line wedding dress",
    "color": "white",
    "pattern": "lace embroidery"
  }
}
```

##### 3. Virtual Try-On (기본)
```bash
curl -X POST "http://localhost:8000/try-on" \
  -F "person_image=@bride.jpg" \
  -F "clothing_image=@dress.jpg" \
  -F "style=default"
```

##### 4. Virtual Try-On (웨딩드레스)
```bash
curl -X POST "http://localhost:8000/try-on/wedding" \
  -F "person_image=@bride.jpg" \
  -F "clothing_image=@dress.jpg"
```

##### 5. Virtual Try-On (반복 개선)
```bash
curl -X POST "http://localhost:8000/try-on/iterative" \
  -F "person_image=@bride.jpg" \
  -F "clothing_image=@dress.jpg" \
  -F "iterations=2"
```

응답:
```json
{
  "success": true,
  "image_base64": "base64_encoded_image_data",
  "mime_type": "image/jpeg",
  "person": {...},
  "clothing": {...},
  "prompt": "..."
}
```

#### Python 스크립트 예시

```python
from virtual_tryon import VirtualTryOn

# 초기화
tryon = VirtualTryOn()

# Virtual Try-On 수행
result = tryon.process_with_validation(
    person_image_path="bride.jpg",
    clothing_image_path="wedding_dress.jpg",
    style="wedding"
)

if result["success"]:
    # 이미지 저장
    with open("output.jpg", "wb") as f:
        f.write(result["image"])
    print("성공!")
else:
    print(f"실패: {result['error']}")
```

### C. Streamlit UI

Streamlit 앱 실행:
```bash
streamlit run app.py
```

사용법:
1. 사이드바에서 API 키 입력
2. 드레스 이미지 업로드
3. 자동 분석 또는 수동 분석
4. 결과 확인 및 관리

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

### 백엔드
- **Python 3.9+**
- **Anthropic Claude API** - 드레스 이미지 분석 및 텍스트 생성
- **Google Gemini API** - Virtual Try-On 이미지 생성
- **FastAPI** - RESTful API 서버
- **Pydantic** - 데이터 검증
- **Pillow** - 이미지 처리

### 프론트엔드
- **Streamlit** - 웹 UI

### 기타
- **python-dotenv** - 환경변수 관리
- **uvicorn** - ASGI 서버

## Streamlit 버전 업그레이드

  - 앱 실행:
    ```bash
    streamlit run app.py
    ```
- 사용법:
  - 사이드바에서 `ANTHROPIC_API_KEY` 입력 또는 `.env` 사용.
  - 이미지 업로드 → [선택 이미지 분석 및 저장] 클릭.
  - 하단 표에서 보기 모드(플랫/원본 JSON) 전환.
  - id 쉼표입력 후 복사/JSON 다운로드/선택 삭제 가능. 새로고침 버튼 제공.

변경 규모: 중간

요약:
- `app.py` 추가: 업로드→Anthropic 분석→`results.jsonl` 저장, 테이블 뷰, 복사/다운로드/삭제, 새로고침.
- `requirements.txt` 업데이트: `streamlit`, `pandas` 추가.