"""Limited offline parser for UI demonstrations/tests, never a live-model fallback."""

import json
import re
from app.schemas.requirements import Change, Extraction


class DemoExtractor:
    mode = "demo"

    def extract(self, message, state, recent, products):
        text = message.casefold()
        changes = {}

        def put(field, value, clear=False):
            changes[field] = Change(
                field=field,
                action="clear" if clear else "set",
                value_json=None if clear else json.dumps(value),
                evidence=message,
            )

        cases = list(state.use_cases)
        mapping = {
            "programming": ["programming", "coding"],
            "machine_learning": ["machine learning", " ml "],
            "gaming": ["gaming", "games"],
            "creative": ["editing", "creative", "design"],
            "general": ["general coursework", "office", "browsing"],
        }
        for case, phrases in mapping.items():
            if any(p in text for p in phrases) and case not in cases:
                cases.append(case)
        if cases != state.use_cases:
            put("use_cases", cases)
        if "laptop" in text:
            put("category", "laptop")
        elif any(x in text for x in ["phone", "television", "headphone"]):
            put("category", "other")
        if "no fixed budget" in text or "no budget limit" in text:
            put("no_budget", True)
        else:
            pattern = r"(?:budget(?: is| of)?|under|below|around|maximum(?: is)?|max|up to)\s*(?:rs\.?|inr|₹)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(k|lakh)?"
            found = re.search(pattern, text)
            if found:
                value = float(found[1].replace(",", "")) * ({"k": 1000, "lakh": 100000}.get(found[2], 1))
                put("budget_max_inr", int(value))
            elif re.fullmatch(r"\s*(?:₹|inr)?\s*([0-9,]+)\s*(k)?\s*", text):
                f = re.fullmatch(r"\s*(?:₹|inr)?\s*([0-9,]+)\s*(k)?\s*", text)
                put("budget_max_inr", int(f[1].replace(",", "")) * (1000 if f[2] else 1))
        for field, pattern in [
            ("min_ram_gb", r"(\d+)\s*gb\s*(?:of )?ram"),
            ("min_storage_gb", r"(\d+)\s*gb\s*(?:of )?(?:storage|ssd)"),
        ]:
            f = re.search(pattern, text)
            if f:
                put(field, int(f[1]))
        f = re.search(r"(?:under|below|max(?:imum)?(?: weight)?|at most)\s*(\d+(?:\.\d+)?)\s*kg", text)
        if f:
            put("max_weight_kg", float(f[1]))
        if "no longer need" in text and ("gpu" in text or "graphics" in text):
            put("require_dedicated_gpu", None, True)
        elif "must" in text and ("dedicated" in text or "gpu" in text):
            put("require_dedicated_gpu", True)
        if "cloud" in text:
            put("ml_mode", "cloud")
        elif "local" in text:
            put("ml_mode", "local")
        prefs = list(state.preferences)
        for pref, words in {
            "lightweight": ["lightweight", "carry", "portable"],
            "battery": ["long battery"],
            "performance": ["prefer performance"],
            "value": ["best value"],
        }.items():
            if any(word in text for word in words) and pref not in prefs:
                prefs.append(pref)
        if prefs != state.preferences:
            put("preferences", prefs)
        decision = "none"
        if state.pending_budget and re.fullmatch(r"(?:yes|yes please|accept|okay|ok|go ahead)[.! ]*", text):
            decision = "accept"
        elif state.pending_budget and text.strip() in ("no", "no thanks", "reject"):
            decision = "reject"
        intent = (
            "compare"
            if "compare" in text
            else "details"
            if "second one" in text or "first one" in text
            else "recommend"
        )
        ids = []
        if products and "first one" in text:
            ids = [products[0]["id"]]
        if len(products) > 1 and "second one" in text:
            ids = [products[1]["id"]]
        return Extraction(
            intent=intent,
            changes=list(changes.values()),
            conflicts=[],
            proposal_decision=decision,
            product_ids=ids,
        )
