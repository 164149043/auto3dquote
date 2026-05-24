"""验证码生成与校验"""

import base64
import random
import string
import time
from collections import defaultdict
from io import BytesIO

from fastapi import HTTPException, status

# 验证码存储: {captcha_id: {"code": "ABCD", "expires": timestamp}}
_captcha_store: dict[str, dict] = {}

# IP 频率限制: {ip: [timestamp, timestamp, ...]}
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# 配置
CAPTCHA_EXPIRE_SECONDS = 300  # 验证码 5 分钟有效
RATE_LIMIT_WINDOW = 3600  # 1 小时窗口
RATE_LIMIT_MAX = 5  # 每小时最多 5 次注册


def generate_captcha(length: int = 4) -> tuple[str, str]:
    """生成验证码，返回 (captcha_id, base64_png_image)"""
    captcha_id = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=length))

    # 生成简单图片
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (120, 40), (30, 30, 50))
        draw = ImageDraw.Draw(img)

        # 添加干扰线
        for _ in range(4):
            x1, y1 = random.randint(0, 120), random.randint(0, 40)
            x2, y2 = random.randint(0, 120), random.randint(0, 40)
            draw.line([(x1, y1), (x2, y2)], fill=(80, 80, 100), width=1)

        # 绘制文字
        for i, ch in enumerate(code):
            x = 10 + i * 25
            y = random.randint(5, 12)
            color = (
                random.randint(150, 255),
                random.randint(150, 255),
                random.randint(50, 200),
            )
            draw.text((x, y), ch, fill=color)

        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        image_data_uri = f"data:image/png;base64,{b64}"
    except ImportError:
        # 没有 PIL，用 SVG 替代
        svg_parts = []
        for i, ch in enumerate(code):
            x = 15 + i * 25
            y = random.randint(18, 28)
            color = f"#{random.randint(0x80, 0xFF):02x}{random.randint(0x80, 0xFF):02x}{random.randint(0x40, 0xFF):02x}"
            svg_parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="22" font-weight="bold">{ch}</text>')
        # 干扰线
        for _ in range(3):
            x1, y1 = random.randint(0, 120), random.randint(0, 40)
            x2, y2 = random.randint(0, 120), random.randint(0, 40)
            svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#555" stroke-width="1"/>')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40" style="background:#1e1e32">{"".join(svg_parts)}</svg>'
        b64 = base64.b64encode(svg.encode()).decode()
        image_data_uri = f"data:image/svg+xml;base64,{b64}"

    # 存储
    _captcha_store[captcha_id] = {
        "code": code,
        "expires": time.time() + CAPTCHA_EXPIRE_SECONDS,
    }

    # 清理过期验证码
    now = time.time()
    expired = [k for k, v in _captcha_store.items() if v["expires"] < now]
    for k in expired:
        del _captcha_store[k]

    return captcha_id, image_data_uri


def verify_captcha(captcha_id: str, code: str) -> None:
    """校验验证码，失败抛异常"""
    entry = _captcha_store.pop(captcha_id, None)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码已过期或不存在，请刷新验证码",
        )
    if time.time() > entry["expires"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码已过期，请刷新验证码",
        )
    if entry["code"].upper() != code.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误",
        )


def check_rate_limit(ip: str) -> None:
    """检查 IP 注册频率，超限抛异常"""
    now = time.time()
    records = _rate_limit_store[ip]
    # 清理过期记录
    records[:] = [t for t in records if now - t < RATE_LIMIT_WINDOW]
    if len(records) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"注册过于频繁，每小时最多 {RATE_LIMIT_MAX} 次",
        )
    records.append(now)
