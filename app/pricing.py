from decimal import Decimal

# (input, output) in USD per 1M tokens
PRICING = {
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "gpt-4o":      (Decimal("2.50"), Decimal("10.00")),

    "openai/gpt-oss-20b": (Decimal("0.00"), Decimal("0")),
    "openai/gpt-oss-120b": (Decimal("00"), Decimal("0")),
    "qwen/qwen3.8-27b": (Decimal("0"), Decimal("0")),
    "minimax/minimax-m3.1-flash:free": (Decimal("0"), Decimal("0")),
    "anthropic/claude-opus-5.5": (Decimal("4"), Decimal("20")),
    "xingchen-agi/xing4.0-29b-a4b:free": (Decimal("0"), Decimal("0"))

}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:

    if model not in PRICING:
        print(f"[pricing] Unknown model: {model}, assuming free")
        return Decimal("0.00")  # Unknown model, assume free
    input_price, output_price = PRICING[model]

    cost = (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000

    return cost