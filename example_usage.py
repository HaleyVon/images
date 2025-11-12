#!/usr/bin/env python3
"""
Virtual Try-On 사용 예제
"""

import os
from pathlib import Path
from virtual_tryon import VirtualTryOn
from image_validator import ImageValidator


def example1_basic_tryon():
    """예제 1: 기본 Virtual Try-On"""
    print("="*80)
    print("예제 1: 기본 Virtual Try-On")
    print("="*80)

    tryon = VirtualTryOn()

    # Virtual Try-On 수행
    result = tryon.process_with_validation(
        person_image_path="examples/person.jpg",
        clothing_image_path="examples/dress.jpg",
        style="default"
    )

    if result["success"]:
        # 이미지 저장
        output_path = "output/example1_result.jpg"
        os.makedirs("output", exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(result["image"])

        print(f"\n✓ 성공! 결과가 저장되었습니다: {output_path}")
        print(f"  사람: {result['person']['description']}")
        print(f"  의류: {result['clothing']['description']}")
    else:
        print(f"\n✗ 실패: {result['error']}")


def example2_wedding_dress():
    """예제 2: 웨딩드레스 Virtual Try-On"""
    print("\n" + "="*80)
    print("예제 2: 웨딩드레스 Virtual Try-On")
    print("="*80)

    tryon = VirtualTryOn()

    # 웨딩드레스 Virtual Try-On 수행
    result = tryon.process_with_validation(
        person_image_path="examples/bride.jpg",
        clothing_image_path="examples/wedding_dress.jpg",
        style="wedding"
    )

    if result["success"]:
        # 이미지 저장
        output_path = "output/example2_wedding_result.jpg"
        os.makedirs("output", exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(result["image"])

        print(f"\n✓ 성공! 결과가 저장되었습니다: {output_path}")
        print(f"\n생성된 프롬프트:")
        print(result["prompt"][:200] + "...")
    else:
        print(f"\n✗ 실패: {result['error']}")


def example3_iterative_refinement():
    """예제 3: 반복 개선 모드"""
    print("\n" + "="*80)
    print("예제 3: 반복 개선 모드 (최고 품질)")
    print("="*80)

    tryon = VirtualTryOn()

    # 반복 개선 모드로 Virtual Try-On 수행
    result = tryon.iterative_try_on(
        person_image_path="examples/bride.jpg",
        clothing_image_path="examples/wedding_dress.jpg",
        iterations=2
    )

    if result["success"]:
        # 이미지 저장
        output_path = "output/example3_iterative_result.jpg"
        os.makedirs("output", exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(result["image"])

        print(f"\n✓ 성공! 결과가 저장되었습니다: {output_path}")
    else:
        print(f"\n✗ 실패: {result['error']}")


def example4_image_validation():
    """예제 4: 이미지 검증"""
    print("\n" + "="*80)
    print("예제 4: 이미지 검증")
    print("="*80)

    validator = ImageValidator()

    # 사람 이미지 검증
    print("\n[사람 이미지 검증]")
    person_result = validator.validate_person_image(Path("examples/person.jpg"))

    print(f"  사람 포함: {person_result.is_person}")
    print(f"  설명: {person_result.description}")
    print(f"  신체 가시성: {person_result.body_visible}")
    print(f"  적합한 포즈: {person_result.pose_suitable}")

    # 의류 이미지 검증
    print("\n[의류 이미지 검증]")
    clothing_result = validator.validate_clothing_image(Path("examples/dress.jpg"))

    print(f"  의류 여부: {clothing_result.is_clothing}")
    print(f"  의류 타입: {clothing_result.clothing_type}")
    print(f"  설명: {clothing_result.description}")
    print(f"  색상: {clothing_result.color}")
    print(f"  패턴: {clothing_result.pattern}")


def example5_custom_prompt():
    """예제 5: 커스텀 프롬프트 사용"""
    print("\n" + "="*80)
    print("예제 5: 커스텀 프롬프트 사용")
    print("="*80)

    from image_validator import Person, ClothingItem
    from prompt_generator import PromptGenerator

    # 수동으로 Person 및 ClothingItem 정의
    person = Person(
        is_person=True,
        description="elegant young woman in her 20s, standing gracefully",
        body_visible=True,
        pose_suitable=True
    )

    clothing = ClothingItem(
        is_clothing=True,
        clothing_type="evening gown",
        description="luxurious red evening gown with intricate beading",
        color="deep red",
        pattern="geometric beading pattern"
    )

    # 커스텀 카메라 설정
    camera_settings = {
        "shot_type": "Full body portrait",
        "focal_length": "85mm (portrait lens)",
        "angle": "Slightly from below for elegance",
        "depth_of_field": "Shallow (f/1.8) for dramatic look"
    }

    # 향상된 프롬프트 생성
    prompt_gen = PromptGenerator()
    prompt = prompt_gen.generate_enhanced_prompt(
        person=person,
        clothing=clothing,
        style="default",
        camera_settings=camera_settings
    )

    print("\n생성된 프롬프트:")
    print(prompt)


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("Virtual Try-On 사용 예제")
    print("="*80 + "\n")

    # 예제 실행
    try:
        # 주의: 실제 이미지 파일이 examples/ 폴더에 있어야 합니다.
        # 예제 1~3은 실제 이미지가 있을 때 실행하세요.

        # example1_basic_tryon()
        # example2_wedding_dress()
        # example3_iterative_refinement()
        # example4_image_validation()
        example5_custom_prompt()

        print("\n" + "="*80)
        print("모든 예제가 완료되었습니다!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
