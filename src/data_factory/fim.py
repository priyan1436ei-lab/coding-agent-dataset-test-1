"""Fill-in-the-Middle (FIM) transformation pipeline for code completion pretraining."""
import argparse
import json
import logging
import random
from typing import Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fim")

# Standard FIM sentinel tokens (Qwen / StarCoder / DeepSeek format)
FIM_PREFIX = "<fim_prefix>"
FIM_SUFFIX = "<fim_suffix>"
FIM_MIDDLE = "<fim_middle>"

def transform_to_fim(
    text: str,
    fim_rate: float = 0.5,
    spm_prob: float = 0.5,
    seed: Optional[int] = None
) -> Tuple[str, bool]:
    """Transform code string into FIM (Prefix, Suffix, Middle) format with given probability.
    Returns (transformed_text, was_fim_applied).
    """
    if seed is not None:
        random.seed(seed)

    if random.random() > fim_rate or len(text) < 40:
        return text, False

    lines = text.splitlines(keepends=True)
    if len(lines) < 3:
        # Character-level split for short snippets
        cut1 = random.randint(1, len(text) // 3)
        cut2 = random.randint(cut1 + 1, (len(text) * 2) // 3)
        prefix = text[:cut1]
        middle = text[cut1:cut2]
        suffix = text[cut2:]
    else:
        # Line-level split
        line_count = len(lines)
        cut1 = random.randint(1, line_count // 3)
        cut2 = random.randint(cut1 + 1, (line_count * 2) // 3)
        prefix = "".join(lines[:cut1])
        middle = "".join(lines[cut1:cut2])
        suffix = "".join(lines[cut2:])

    # Choose between SPM (Prefix-Suffix-Middle) and PSM (Suffix-Prefix-Middle)
    if random.random() < spm_prob:
        # SPM Mode
        fim_text = f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}{middle}"
    else:
        # PSM Mode
        fim_text = f"{FIM_PREFIX}{suffix}{FIM_SUFFIX}{prefix}{FIM_MIDDLE}{middle}"

    return fim_text, True

def process_file_with_fim(input_jsonl: str, output_jsonl: str, fim_rate: float = 0.5) -> Dict[str, Any]:
    """Apply FIM transformation across JSONL code corpus."""
    total = 0
    fim_applied = 0
    with open(input_jsonl, "r", encoding="utf-8") as in_f, open(output_jsonl, "w", encoding="utf-8") as out_f:
        for line in in_f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            total += 1
            
            # Find assistant code or raw content
            for msg in record.get("messages", []):
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    transformed, applied = transform_to_fim(content, fim_rate=fim_rate)
                    if applied:
                        fim_applied += 1
                        msg["content"] = transformed
                        record["is_fim"] = True
                        break

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"FIM complete: {fim_applied}/{total} records transformed ({round(fim_applied/max(1, total)*100, 1)}%)")
    return {"total": total, "fim_applied": fim_applied, "fim_rate_pct": round(fim_applied/max(1, total)*100, 2)}
