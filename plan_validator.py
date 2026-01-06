from pathlib import Path

ROOT = Path.cwd()
PLAN_PATH = ROOT / "PLAN.md"

# ----------------------
# Validator Rules
# ----------------------
REQUIRED_TAGS = ["<ANALYSIS>", "<FILES_TO_CHANGE>", "<PLAN_STEPS>", "<MEMORY_UPDATE>"]
MAX_ANALYSIS_SENTENCES = 5
MAX_PLAN_STEPS = 10

def read_plan():
    if not PLAN_PATH.exists():
        print("❌ PLAN.md not found!")
        return None
    return PLAN_PATH.read_text(encoding="utf-8")

def validate_plan(content: str):
    errors = []

    # 1. Required tags
    for tag in REQUIRED_TAGS:
        if tag not in content:
            errors.append(f"Missing required tag: {tag}")

    # 2. ANALYSIS length
    try:
        analysis_text = content.split("<ANALYSIS>")[1].split("</ANALYSIS>")[0].strip()
        sentences = [s for s in analysis_text.split(".") if s.strip()]
        if len(sentences) > MAX_ANALYSIS_SENTENCES:
            errors.append(f"ANALYSIS exceeds {MAX_ANALYSIS_SENTENCES} sentences")
    except IndexError:
        errors.append("ANALYSIS section missing or malformed")

    # 3. PLAN_STEPS count
    try:
        steps_text = content.split("<PLAN_STEPS>")[1].split("</PLAN_STEPS>")[0].strip().splitlines()
        steps = [s for s in steps_text if s.strip() and not s.startswith("#")]
        if len(steps) > MAX_PLAN_STEPS:
            errors.append(f"PLAN_STEPS exceeds {MAX_PLAN_STEPS} steps")
    except IndexError:
        errors.append("PLAN_STEPS section missing or malformed")

    # 4. FILES_TO_CHANGE not empty
    try:
        files_text = content.split("<FILES_TO_CHANGE>")[1].split("</FILES_TO_CHANGE>")[0].strip().splitlines()
        files = [f for f in files_text if f.strip() and not f.startswith("#")]
        if not files:
            errors.append("FILES_TO_CHANGE is empty")
    except IndexError:
        errors.append("FILES_TO_CHANGE section missing or malformed")

    # 5. MEMORY_UPDATE presence
    if "<MEMORY_UPDATE>" not in content or "</MEMORY_UPDATE>" not in content:
        errors.append("Missing MEMORY_UPDATE section")

    return errors

def run_validator():
    content = read_plan()
    if not content:
        return False

    errors = validate_plan(content)
    if errors:
        print("❌ PLAN validation failed:")
        for err in errors:
            print(f"  - {err}")
        print("🚫 ACT MUST REFUSE execution until PLAN is valid.")
        return False
    else:
        print("✅ PLAN validation passed. Safe for ACT execution.")
        return True

if __name__ == "__main__":
    run_validator()
