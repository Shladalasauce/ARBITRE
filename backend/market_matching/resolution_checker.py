import re
from datetime import datetime


RISK_TERMS = {
    "inclusive/exclusive": (r"\bat least\b|\bor more\b", r"\bmore than\b|\bgreater than\b"),
    "cancellation": (r"cancel|void", r"cancel|void"),
    "postponement": (r"postpon", r"postpon"),
    "recount": (r"recount", r"recount"),
}


def rule_differences(a: str, b: str, close_a: datetime | None, close_b: datetime | None,
                     source_a: str = "", source_b: str = "") -> list[str]:
    differences: list[str] = []
    al, bl = a.lower(), b.lower()
    if close_a and close_b and abs((close_a - close_b).total_seconds()) > 3600:
        differences.append(f"Cutoff differs: {close_a.isoformat()} vs {close_b.isoformat()}")
    if source_a and source_b and source_a.lower() != source_b.lower():
        differences.append(f"Settlement sources differ: {source_a} vs {source_b}")
    nums_a = set(re.findall(r"(?<!\w)\d+(?:\.\d+)?", al))
    nums_b = set(re.findall(r"(?<!\w)\d+(?:\.\d+)?", bl))
    if nums_a and nums_b and nums_a != nums_b:
        differences.append("Resolution rules contain different numeric thresholds")
    if ("at least" in al) != ("at least" in bl) or ("more than" in al) != ("more than" in bl):
        differences.append("Possible inclusive/exclusive threshold difference")
    for label in ("cancel", "void", "postpon", "recount"):
        if (label in al) != (label in bl):
            differences.append(f"Only one contract explicitly addresses {label} conditions")
    return differences

