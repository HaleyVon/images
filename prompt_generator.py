#!/usr/bin/env python3
"""
Prompt Generator Module
Virtual Try-On을 위한 프롬프트 생성 모듈
"""

from typing import Dict, Any
from image_validator import Person, ClothingItem


class PromptGenerator:
    """Virtual Try-On 프롬프트 생성 클래스"""

    @staticmethod
    def generate_try_on_prompt(person: Person, clothing: ClothingItem) -> str:
        """
        컨텍스트 기반 최적 프롬프트 생성

        Args:
            person: 사람 이미지 분석 결과
            clothing: 의류 이미지 분석 결과

        Returns:
            생성된 프롬프트
        """
        base_prompt = f"""
You are an expert fashion visualization AI specializing in realistic virtual try-on experiences.

Task: Generate a photorealistic image of {person.description} wearing {clothing.description}.

Requirements:
1. Identity Preservation:
   - Keep the subject's face, skin tone, and body shape EXACTLY as in the original photo
   - Do not modify facial features, hair, or body proportions

2. Clothing Accuracy:
   - Reproduce the {clothing.clothing_type} with 100% color accuracy
   - Show all patterns, textures, and design details clearly
   - Ensure realistic fabric draping based on body shape

3. Technical Quality:
   - Professional studio lighting (soft, even, no harsh shadows)
   - Clean white background (#FFFFFF)
   - Sharp focus on clothing details
   - Natural pose and proportions

4. Realism:
   - Photographic quality (not illustrated or cartoon-like)
   - Natural shadows and highlights
   - Realistic fabric behavior and fit

Do not change the input aspect ratio. Output only the final image.
"""
        return base_prompt.strip()

    @staticmethod
    def generate_wedding_dress_prompt(person: Person, clothing: ClothingItem) -> str:
        """
        웨딩드레스 특화 프롬프트 생성

        Args:
            person: 신부 이미지 분석 결과
            clothing: 웨딩드레스 이미지 분석 결과

        Returns:
            생성된 프롬프트
        """
        prompt = f"""
You are a luxury bridal fashion photographer's AI assistant.

Create a stunning bridal portrait showing the bride wearing this wedding dress.

BRIDE: {person.description}
DRESS: {clothing.description}

BRIDAL PHOTOGRAPHY STANDARDS:
1. Preserve the bride's natural beauty and facial features completely
2. Show the wedding dress with exceptional detail:
   - Lace patterns and embroidery
   - Beading and embellishments
   - Fabric flow and train
3. Professional bridal photography lighting:
   - Soft, flattering light
   - Subtle highlights on dress details
   - Romantic atmosphere
4. Elegant pose suitable for bridal portraits
5. Clean, bright background (soft white or cream)

QUALITY: Magazine-quality bridal photography
STYLE: Timeless, elegant, romantic

The bride should look radiant and the dress should look absolutely stunning.
Do not change the input aspect ratio. Output only the final image.
"""
        return prompt.strip()

    @staticmethod
    def generate_enhanced_prompt(
        person: Person,
        clothing: ClothingItem,
        style: str = "default",
        camera_settings: Dict[str, Any] = None
    ) -> str:
        """
        향상된 프롬프트 생성 (추가 컨트롤 옵션)

        Args:
            person: 사람 이미지 분석 결과
            clothing: 의류 이미지 분석 결과
            style: 스타일 (default, wedding, casual, formal)
            camera_settings: 카메라 설정 (optional)

        Returns:
            생성된 프롬프트
        """
        # 기본 프롬프트 선택
        if style == "wedding":
            base = PromptGenerator.generate_wedding_dress_prompt(person, clothing)
        else:
            base = PromptGenerator.generate_try_on_prompt(person, clothing)

        # 카메라 설정 추가 (제공된 경우)
        if camera_settings:
            camera_instructions = "\n\nCamera Settings:\n"
            if "shot_type" in camera_settings:
                camera_instructions += f"- Shot type: {camera_settings['shot_type']}\n"
            if "focal_length" in camera_settings:
                camera_instructions += f"- Focal length: {camera_settings['focal_length']}\n"
            if "angle" in camera_settings:
                camera_instructions += f"- Angle: {camera_settings['angle']}\n"
            if "depth_of_field" in camera_settings:
                camera_instructions += f"- Depth of field: {camera_settings['depth_of_field']}\n"

            base += camera_instructions

        return base


def main():
    """테스트용 메인 함수"""
    # 테스트 데이터
    person = Person(
        is_person=True,
        description="young woman, standing, front-facing, wearing casual clothes",
        body_visible=True,
        pose_suitable=True
    )

    clothing = ClothingItem(
        is_clothing=True,
        clothing_type="wedding dress",
        description="elegant white A-line wedding dress with lace bodice and flowing tulle skirt",
        color="white",
        pattern="lace embroidery"
    )

    # 프롬프트 생성 테스트
    print("=== 기본 프롬프트 ===")
    basic_prompt = PromptGenerator.generate_try_on_prompt(person, clothing)
    print(basic_prompt)

    print("\n" + "="*80 + "\n")

    print("=== 웨딩드레스 프롬프트 ===")
    wedding_prompt = PromptGenerator.generate_wedding_dress_prompt(person, clothing)
    print(wedding_prompt)

    print("\n" + "="*80 + "\n")

    print("=== 향상된 프롬프트 (카메라 설정 포함) ===")
    camera_settings = {
        "shot_type": "Full body portrait",
        "focal_length": "50mm (portrait lens)",
        "angle": "Eye level, straight on",
        "depth_of_field": "Shallow (f/2.8) for professional look"
    }
    enhanced_prompt = PromptGenerator.generate_enhanced_prompt(
        person, clothing, style="wedding", camera_settings=camera_settings
    )
    print(enhanced_prompt)


if __name__ == "__main__":
    main()
