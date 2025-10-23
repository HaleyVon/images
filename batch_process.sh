#!/bin/bash

# 배치 처리 스크립트
# 현재 디렉토리의 모든 PNG 이미지를 처리합니다

echo "드레스 이미지 배치 처리 시작..."
echo ""

# 처리할 이미지 파일 패턴 설정 (기본: PNG)
PATTERN="${1:-*.png}"

# 카운터 초기화
count=0
success=0
fail=0

# 각 이미지 파일 처리
for img in $PATTERN; do
  # 파일이 실제로 존재하는지 확인 (글로브 패턴이 매칭되지 않은 경우 방지)
  if [ ! -f "$img" ]; then
    continue
  fi

  # 결과 파일이 이미 존재하는지 확인
  result_file="${img%.*}_result.json"
  if [ -f "$result_file" ]; then
    echo "⏭️  건너뛰기: $img (이미 처리됨)"
    continue
  fi

  count=$((count + 1))
  echo "[$count] 처리 중: $img"

  # 이미지 처리
  if python3 dress_prompt_generator.py "$img"; then
    success=$((success + 1))
    echo "✓ 완료: $result_file"
  else
    fail=$((fail + 1))
    echo "✗ 실패: $img"
  fi

  echo ""
done

# 결과 요약
echo "========================================"
echo "배치 처리 완료"
echo "========================================"
echo "처리된 이미지: $count"
echo "성공: $success"
echo "실패: $fail"
echo "========================================"
