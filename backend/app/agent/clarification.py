def clarification_target(r):
    if r.category not in ("laptop", "laptops"):
        return (
            "This catalogue currently contains synthetic laptops only. Would you like help choosing a laptop?",
            "category",
        )
    if r.conflicts:
        return ("Please clarify before I change the search: " + " ".join(r.conflicts), "conflicts")
    has_specs = any(
        [
            r.min_ram_gb,
            r.min_storage_gb,
            r.require_dedicated_gpu is not None,
            r.max_weight_kg,
            r.min_battery_hours,
            r.required_features,
        ]
    )
    if not r.use_cases and not has_specs:
        return (
            "What will you mainly use the laptop for: general coursework, programming, gaming, creative work, or machine learning?",
            "use_cases",
        )
    if r.budget_max_inr is None and not r.no_budget:
        return (
            "What is your maximum budget in INR? You can also say you have no fixed budget.",
            "budget_max_inr",
        )
    if "machine_learning" in r.use_cases and r.ml_mode is None and r.require_dedicated_gpu is None:
        attempts = r.clarification_attempts.get("ml_mode", 0)
        if attempts >= 2:
            return (None, None)
        return (
            "Will you run machine-learning experiments locally on the laptop, or mainly use cloud platforms?",
            "ml_mode",
        )
    return (None, None)


def clarification(r):
    question, _ = clarification_target(r)
    return question
