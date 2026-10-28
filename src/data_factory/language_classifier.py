"""High-accuracy language classifier supporting 45+ languages from A to Z."""
import json
import os
import re
from typing import Dict, Any, Optional

TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "../../data/catalogue/LANGUAGE_TAXONOMY.json")

class LanguageClassifier:
    def __init__(self, taxonomy_path: str = TAXONOMY_PATH):
        self.taxonomy = {}
        self.ext_to_lang: Dict[str, str] = {}
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.taxonomy = data.get("languages", {})
                for lang, meta in self.taxonomy.items():
                    for ext in meta.get("extensions", []):
                        self.ext_to_lang[ext.lower()] = lang

        # Keyword signature patterns for content-based classification
        self.signatures = [
            (re.compile(r"\b(def\s+\w+|import\s+numpy|import\s+os|class\s+\w+:)\b"), "Python"),
            (re.compile(r"\b(public\s+class\s+\w+|public\s+static\s+void\s+main)\b"), "Java"),
            (re.compile(r"\b(using\s+System;|namespace\s+\w+|Console\.WriteLine)\b"), "C#"),
            (re.compile(r"\b(#include\s+<iostream>|std::cout|template\s*<typename)\b"), "C++"),
            (re.compile(r"\b(#include\s+<stdio\.h>|int\s+main\s*\()\b"), "C"),
            (re.compile(r"\b(fn\s+main|let\s+mut|impl\s+\w+|println!)\b"), "Rust"),
            (re.compile(r"\b(package\s+main|func\s+main\s*\(\)|fmt\.Println)\b"), "Go"),
            (re.compile(r"\b(const\s+\w+\s*=|console\.log|import\s+React)\b"), "JavaScript"),
            (re.compile(r"\b(interface\s+\w+|type\s+\w+\s*=|:\s*string\s*=)\b"), "TypeScript"),
            (re.compile(r"\b(fun\s+main\s*\(|val\s+\w+\s*:|package\s+[a-z.]+)\b"), "Kotlin"),
            (re.compile(r"\b(import\s+SwiftUI|func\s+\w+\s*\(|var\s+body:\s*some\s+View)\b"), "Swift"),
            (re.compile(r"\b(SELECT\s+.*FROM|CREATE\s+TABLE|INSERT\s+INTO)\b", re.IGNORECASE), "SQL"),
            (re.compile(r"\b(defmodule\s+\w+|def\s+\w+\s+do)\b"), "Elixir"),
            (re.compile(r"\b(module\s+\w+|module\s+type\s+of)\b"), "OCaml"),
            (re.compile(r"\b(with\s+Ada\.\w+|procedure\s+\w+\s+is)\b", re.IGNORECASE), "Ada"),
            (re.compile(r"\b(IDENTIFICATION\s+DIVISION|PROGRAM-ID)\b", re.IGNORECASE), "COBOL"),
            (re.compile(r"\b(sub\s+\w+\s*\{|my\s+\$\w+)\b"), "Perl"),
            (re.compile(r"\b(<?php|\$\w+\s*=)\b"), "PHP"),
            (re.compile(r"\b(def\s+\w+\s*\n|require\s+['\"]rails['\"])\b"), "Ruby"),
            (re.compile(r"\b(contract\s+\w+|pragma\s+solidity)\b"), "Solidity"),
            (re.compile(r"\b(pub\s+fn\s+main|const\s+std\s*=\s*@import)\b"), "Zig"),
            (re.compile(r"\b(module\s+\w+\s*\(|always\s*@)\b"), "Verilog"),
            (re.compile(r"\b(entity\s+\w+\s+is|architecture\s+\w+\s+of)\b", re.IGNORECASE), "VHDL")
        ]

    def classify_by_extension(self, filename: str) -> Optional[str]:
        """Lookup language strictly from file extension."""
        ext = os.path.splitext(filename)[1].lower()
        return self.ext_to_lang.get(ext)

    def classify_content(self, text: str, filename_hint: Optional[str] = None) -> str:
        """Identify language using filename hint fallback to signature match."""
        if filename_hint:
            lang = self.classify_by_extension(filename_hint)
            if lang:
                return lang

        for pattern, lang_name in self.signatures:
            if pattern.search(text):
                return lang_name

        return "Unknown"
