"""Validate tokenizer and chat template compatibility with AetherCoder JSONL format."""
import argparse
import json
import logging
import os
import sys

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tokenizer_check")

def check_chat_template_rendering(
    manifest_file: str,
    model_id: str = "Qwen/Qwen2.5-Coder-1.5B",
    max_samples: int = 5
) -> dict:
    """Validate that sample records from manifest format cleanly through AutoTokenizer."""
    from transformers import AutoTokenizer

    logger.info(f"Loading tokenizer for: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    
    results = {
        "model_id": model_id,
        "vocab_size": tokenizer.vocab_size,
        "chat_template_defined": bool(tokenizer.chat_template),
        "samples_tested": 0,
        "token_lengths": [],
        "sample_renders": []
    }

    for idx, record in enumerate(stream_jsonl(manifest_file, max_records=max_samples)):
        messages = record.get("messages", [])
        try:
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            tokens = tokenizer.encode(rendered)
            results["samples_tested"] += 1
            results["token_lengths"].append(len(tokens))
            if idx == 0:
                results["sample_renders"].append({
                    "record_id": record.get("id"),
                    "token_count": len(tokens),
                    "rendered_head": rendered[:300]
                })
        except Exception as e:
            logger.error(f"Failed to apply chat template to record {record.get('id')}: {e}")
            raise

    logger.info(f"Successfully validated {results['samples_tested']} records. Avg tokens: {sum(results['token_lengths']) / max(1, len(results['token_lengths'])):.1f}")
    return results

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Tokenizer & Chat Template Validator")
    parser.add_argument("--manifest", type=str, required=True, help="Path to JSONL records")
    parser.add_argument("--model-id", type=str, default="Qwen/Qwen2.5-Coder-1.5B", help="Model name or local path")
    parser.add_argument("--max-samples", type=int, default=5, help="Number of records to test")
    args = parser.parse_args()

    res = check_chat_template_rendering(args.manifest, model_id=args.model_id, max_samples=args.max_samples)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
