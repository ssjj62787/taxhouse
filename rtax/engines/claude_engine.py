"""선택형 엔진: Claude 멀티모달 API. 기울어지거나 반사·흐림이 있는 사진에서
Tesseract보다 훨씬 정확하게 읽지만, Anthropic API 키와 사용량만큼의 비용이 필요합니다.

사용법:
  1) pip install anthropic
  2) 환경변수 ANTHROPIC_API_KEY 설정
  3) rtax/config.py 의 OCR_ENGINE = "claude" 로 변경 (또는 RTAX_OCR_ENGINE=claude)
"""
import base64
import io

from rtax import config
from rtax.engines.base import OCREngine

_PROMPT = (
    "이 이미지는 한국 부동산 매매 관련 증빙(계약서/영수증/증명원)입니다. "
    "이미지에 보이는 글자를 줄바꿈과 표 구조를 최대한 유지하면서 그대로 텍스트로 옮겨 적으세요. "
    "추측하거나 보완하지 말고, 읽을 수 없는 부분은 [판독불가]로 표시하세요. "
    "설명이나 요약 없이 옮겨 적은 텍스트만 출력하세요."
)


class ClaudeVisionEngine(OCREngine):
    name = "claude"

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. "
                "환경변수를 설정하거나 OCR_ENGINE을 'tesseract'로 두세요."
            )
        import anthropic
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def recognize(self, image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        response = self._client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/png", "data": b64,
                    }},
                    {"type": "text", "text": _PROMPT},
                ],
            }],
        )
        parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts)
