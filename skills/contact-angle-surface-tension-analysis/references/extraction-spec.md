# Contact Angle Extraction Spec (Multimodal / OCR)

## Per-image required JSON

For each image, extract contact-angle values and output:

```json
{"left_ca": 74.76, "right_ca": 75.30, "average_ca": 75.03, "unit": "degree"}
```

Rules:

- `left_ca`: left contact angle if visible, else `null`
- `right_ca`: right contact angle if visible, else `null`
- `average_ca`: average angle if visible; when only one angle value is available, write that single value here
- `unit`: always `"degree"` for contact-angle screenshots

## Interpretation boundary

- `< 90 deg`: hydrophilic or borderline
- `>= 90 deg` and `< 150 deg`: hydrophobic
- `>= 150 deg`: superhydrophobic

## OCR / multimodal fallback order

1. OCR first (fast and scriptable) for all images.
2. If OCR fails to read numeric overlays, run multimodal extraction per image using the same output schema.
3. Keep failed fields as `null`; do not guess values.

## Optional multimodal prompt template (Chinese)

Use this prompt when a multimodal model is available:

```text
你是一个专业的科研数据提取助手。请从这张接触角测试图片中提取接触角数值。

输出要求：
1. 识别图片中的左接触角 (Left CA)、右接触角 (Right CA) 和平均接触角 (Average CA)。
2. 如果图片只提供了一个数值（如 Angle: 31.65），则将其视为平均值。
3. 如果图片提供了左右两个数值，请分别记录。
4. 仅输出 JSON 格式，包含字段：left_ca, right_ca, average_ca, unit。
5. 如果某个数值无法找到，请填 null。
```

## Optional image base64 helper

```python
import base64

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
```
