import re


class FindingList(list):
    def __init__(self, findings: list[dict[str, object]], chunk_count: int) -> None:
        super().__init__(findings)
        self.chunk_count = chunk_count


def _count_chunks(diff_text: str) -> int:
    max_chunk_bytes = 65536
    files: list[tuple[str, str]] = []
    current_file: str | None = None
    current_content: list[str] = []

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            if current_file is not None:
                files.append((current_file, "\n".join(current_content)))
            current_file = line[4:].strip()
            current_content = []
            continue

        if current_file is not None:
            current_content.append(line)

    if current_file is not None:
        files.append((current_file, "\n".join(current_content)))

    if not files:
        return 0

    chunks = 0
    current_size = 0
    for _, content in files:
        size = len(content.encode("utf-8"))
        if size > max_chunk_bytes:
            chunks += 1
            current_size = 0
            continue

        if current_size + size > max_chunk_bytes:
            chunks += 1
            current_size = 0

        current_size += size

    if current_size > 0 or not chunks:
        chunks += 1

    return chunks


def review_diff(diff: str, max_findings: int) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    current_path: str | None = None
    current_line: int | None = None
    hunk_header = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    lines = diff.splitlines()
    chunk_count = _count_chunks(diff)

    def add_finding(
        rule_id: str,
        severity: str,
        category: str,
        title: str,
        evidence: str,
        line_value: int,
    ) -> None:
        path_value = current_path or ""
        findings.append(
            {
                "id": f"{rule_id}:{path_value}:{line_value}",
                "path": path_value,
                "line": line_value,
                "ruleId": rule_id,
                "severity": severity,
                "category": category,
                "title": title,
                "evidence": evidence,
            }
        )

    for index, raw_line in enumerate(lines):
        if raw_line.startswith("+++ "):
            candidate = raw_line[4:].strip()
            if candidate.startswith("b/"):
                candidate = candidate[2:].strip()
                if candidate and candidate != "/dev/null":
                    current_path = candidate
            continue

        if raw_line.startswith("@@"):
            match = hunk_header.match(raw_line)
            if match:
                current_line = int(match.group(1))
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            evidence = raw_line[1:]
            if current_line is None:
                current_line = 0

            line_value = current_line
            current_line += 1

            if "eval(" in evidence:
                add_finding("MOCK-001", "critical", "security", "eval usage", evidence, line_value)

            if any(token in evidence.lower() for token in ["apikey", "api_key", "api-key"]):
                add_finding("MOCK-002", "critical", "security", "secret", evidence, line_value)

            if "+" in evidence and any(
                keyword in evidence.upper()
                for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]
            ):
                add_finding(
                    "MOCK-003",
                    "high",
                    "security",
                    "SQL string concatenation",
                    evidence,
                    line_value,
                )

            if "catch" in evidence:
                if index + 1 < len(lines):
                    next_line = lines[index + 1]
                    next_evidence = next_line[1:] if next_line.startswith("+") else ""

                    if next_evidence.strip() == "" or next_evidence.strip() == "{":
                        add_finding(
                            "MOCK-004",
                            "high",
                            "correctness",
                            "swallowed exception",
                            evidence,
                            line_value,
                        )

            if "== null" in evidence or "!= null" in evidence:
                add_finding(
                    "MOCK-005",
                    "medium",
                    "correctness",
                    "loose null comparison",
                    evidence,
                    line_value,
                )

            if "JSON.parse(JSON.stringify(" in evidence:
                add_finding(
                    "MOCK-006",
                    "medium",
                    "performance",
                    "deep-clone via JSON",
                    evidence,
                    line_value,
                )

            if "console.log(" in evidence:
                add_finding(
                    "MOCK-007",
                    "low",
                    "style",
                    "console.log left in",
                    evidence,
                    line_value,
                )

            if "TODO" in evidence or "FIXME" in evidence:
                add_finding("MOCK-008", "low", "style", "unresolved marker", evidence, line_value)

            if any(
                phrase in evidence.lower()
                for phrase in [
                    "ignore previous instructions",
                    "disregard all prior",
                    "you are now",
                ]
            ):
                add_finding(
                    "MOCK-INJ",
                    "critical",
                    "security",
                    "prompt-injection content",
                    evidence,
                    line_value,
                )

            continue

        if raw_line.startswith("-"):
            continue

        if current_line is not None and not raw_line.startswith("@@"):
            current_line += 1

    findings.sort(
        key=lambda item: (
            str(item.get("path", "")),
            int(item.get("line", 0)),
            str(item.get("ruleId", "")),
        )
    )

    seen: set[str] = set()
    unique_findings: list[dict[str, object]] = []
    for item in findings:
        item_id = str(item.get("id", ""))
        if item_id in seen:
            continue
        seen.add(item_id)
        unique_findings.append(item)

    if max_findings <= 0:
        return FindingList([], chunk_count)

    return FindingList(unique_findings[:max_findings], chunk_count)
