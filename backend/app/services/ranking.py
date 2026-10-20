"""Transparent heuristics, not measured hardware performance or confidence."""

from app.services.catalogue import product_dict

TARGETS = {
    "general": (2, 8, 0),
    "programming": (3, 16, 0),
    "gaming": (3, 16, 3),
    "creative": (4, 32, 3),
    "machine_learning": (4, 32, 4),
}


def workload(p, r):
    scores = []
    for use in r.use_cases:
        cpu, ram, gpu = TARGETS[use]
        if use == "machine_learning" and r.ml_mode == "cloud":
            cpu, ram, gpu = 3, 16, 0
        parts = [min(p.cpu_tier / cpu, 1), min(p.ram_gb / ram, 1)]
        if gpu:
            parts.append(min(p.gpu_tier / gpu, 1))
        scores.append(sum(parts) / len(parts))
    return sum(scores) / len(scores) if scores else None


def rank_products(products, r):
    result = []
    for p in products:
        factors, weights = {}, {}
        fit = workload(p, r)
        if fit is not None:
            factors["workload"] = fit
            weights["workload"] = 0.5
        prefs = []
        for pref in r.preferences:
            if pref == "lightweight":
                prefs.append(max(0, min(1, (3 - p.weight_kg) / 2)) if p.weight_kg is not None else 0)
            elif pref == "battery":
                prefs.append(min(p.battery_hours / 12, 1) if p.battery_hours is not None else 0)
            elif pref == "performance":
                prefs.append((p.cpu_tier / 5 + min(p.ram_gb / 32, 1) + p.gpu_tier / 5) / 3)
            elif pref == "value":
                prefs.append(min(1, 40000 / p.price_inr))
        if prefs:
            factors["preferences"] = sum(prefs) / len(prefs)
            weights["preferences"] = 0.3
        if r.budget_max_inr:
            factors["affordability"] = max(0, 1 - p.price_inr / r.budget_max_inr)
            weights["affordability"] = 0.2
        total_weight = sum(weights.values())
        score = sum(factors[k] * weights[k] for k in weights) / total_weight if total_weight else 0
        contributions = {k: round(factors[k] * weights[k] / total_weight, 4) for k in weights}
        reasons, tradeoffs, unknowns = [], [], []
        if r.budget_max_inr:
            reasons.append(
                f"Within your INR {r.budget_max_inr:,} ceiling (INR {r.budget_max_inr - p.price_inr:,} remaining)."
            )
        for value, actual, label in [
            (r.min_ram_gb, p.ram_gb, "GB RAM"),
            (r.min_storage_gb, p.storage_gb, "GB storage"),
        ]:
            if value is not None:
                reasons.append(f"{actual} {label} meets your minimum of {value}.")
        if r.require_dedicated_gpu is not None:
            reasons.append(
                "Meets your dedicated-graphics requirement."
                if r.require_dedicated_gpu
                else "Meets your requirement to avoid dedicated graphics."
            )
        if r.max_weight_kg is not None:
            reasons.append(f"{p.weight_kg:g} kg is within your {r.max_weight_kg:g} kg limit.")
        if r.min_battery_hours is not None:
            reasons.append(f"Catalogue battery estimate {p.battery_hours:g} h meets your stated minimum.")
        if r.required_features:
            reasons.append("Includes required features: " + ", ".join(r.required_features) + ".")
        if r.use_cases:
            reasons.append(
                f"Workload heuristic uses CPU tier {p.cpu_tier}/5 and {p.ram_gb} GB RAM"
                + (f", plus graphics tier {p.gpu_tier}/5." if p.gpu_tier else ".")
            )
        if "lightweight" in r.preferences and p.weight_kg is not None:
            reasons.append(f"Recorded weight is {p.weight_kg:g} kg; lower weight is preferred in ranking.")
        if "battery" in r.preferences and p.battery_hours is not None:
            reasons.append(f"Synthetic battery estimate: {p.battery_hours:g} hours.")
        for attr, label in [
            ("weight_kg", "Weight"),
            ("battery_hours", "Battery duration"),
            ("vram_gb", "VRAM"),
            ("dedicated_gpu", "Dedicated graphics status"),
        ]:
            if getattr(p, attr) is None:
                unknowns.append(label + " is not recorded.")
        for use in r.use_cases:
            _cpu, ram, gpu = TARGETS[use]
            if use == "machine_learning" and r.ml_mode == "cloud":
                _cpu, ram, gpu = 3, 16, 0
            if p.ram_gb < ram:
                tradeoffs.append(
                    f"{p.ram_gb} GB RAM is below this demo's {ram} GB preference target for {use.replace('_', ' ')}."
                )
            if gpu and p.gpu_tier < gpu:
                tradeoffs.append(
                    f"Graphics tier {p.gpu_tier}/5 is below the demo target {gpu}/5 for {use.replace('_', ' ')}."
                )
        if "lightweight" in r.preferences and p.weight_kg is not None and p.weight_kg > 1.8:
            tradeoffs.append(
                f"At {p.weight_kg:g} kg, it is heavier than the demo's 1.8 kg portability reference."
            )
        result.append(
            {
                "product": product_dict(p),
                "score": round(score, 4),
                "score_components": contributions,
                "reasons": reasons or ["Meets all stated mandatory filters."],
                "trade_offs": list(dict.fromkeys(tradeoffs)),
                "unknowns": unknowns,
            }
        )
    result.sort(key=lambda x: (-x["score"], x["product"]["price_inr"], x["product"]["id"]))
    top = result[:2]
    if len(top) == 2:
        for a, b in [(top[0], top[1]), (top[1], top[0])]:
            pa, pb = a["product"], b["product"]
            if pa["price_inr"] > pb["price_inr"]:
                a["trade_offs"].append(
                    f"Costs INR {pa['price_inr'] - pb['price_inr']:,} more than {pb['name']}."
                )
            if pa["ram_gb"] < pb["ram_gb"]:
                a["trade_offs"].append(f"Has {pa['ram_gb']} GB RAM versus {pb['ram_gb']} GB in {pb['name']}.")
            if (
                pa["weight_kg"] is not None
                and pb["weight_kg"] is not None
                and pa["weight_kg"] > pb["weight_kg"]
            ):
                a["trade_offs"].append(
                    f"Weighs {pa['weight_kg']:g} kg versus {pb['weight_kg']:g} kg for {pb['name']}."
                )
    return top
