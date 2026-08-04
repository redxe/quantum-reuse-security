#!/usr/bin/env python3
"""Sync GitHub Issues from one repository into an Airtable table.

Environment variables:
- AIRTABLE_TOKEN (required)
- AIRTABLE_BASE_ID (required, app...)
- AIRTABLE_TABLE_NAME (required)
- GITHUB_REPOSITORY (required outside GitHub Actions, owner/repo)
- GITHUB_TOKEN (optional, improves API rate limits)
- AIRTABLE_SYNC_STATE (optional: open|closed|all, default: all)

Optional Airtable field-name overrides:
- AIRTABLE_FIELD_ISSUE_NUMBER (default: Issue Number)
- AIRTABLE_FIELD_TITLE (default: Title)
- AIRTABLE_FIELD_STATUS (default: Status)
- AIRTABLE_FIELD_URL (default: URL)
- AIRTABLE_FIELD_LABELS (default: Labels)
- AIRTABLE_FIELD_ASSIGNEES (default: Assignees)
- AIRTABLE_FIELD_MILESTONE (default: Milestone)
- AIRTABLE_FIELD_STATE (default: State)
- AIRTABLE_FIELD_REPOSITORY (default: Repository)
- AIRTABLE_FIELD_CREATED_AT (default: Created At)
- AIRTABLE_FIELD_UPDATED_AT (default: Updated At)
- AIRTABLE_FIELD_SYNCED_AT (default: Synced At)

Set any optional field override to an empty string to disable syncing that field.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def http_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url=url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}\n{detail}") from exc


def github_api_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> Any:
    return http_json(method, url, headers, payload)


def field_name(env_name: str, default: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        return default
    # If the variable exists but is empty, treat it as explicitly disabled.
    return value.strip()


def airtable_table_url(base_id: str, table_name: str) -> str:
    return f"https://api.airtable.com/v0/{base_id}/{quote(table_name, safe='')}"


def airtable_find_by_issue_number(
    base_id: str,
    table_name: str,
    token: str,
    issue_field: str,
    issue_number: int,
) -> dict[str, Any] | None:
    formula = f"{{{issue_field}}}={issue_number}"
    params = urlencode({"maxRecords": 1, "filterByFormula": formula})
    url = f"{airtable_table_url(base_id, table_name)}?{params}"
    headers = {"Authorization": f"Bearer {token}"}
    data = http_json("GET", url, headers)
    records = data.get("records", [])
    if records:
        return records[0]
    return None


def airtable_list_records(
    base_id: str,
    table_name: str,
    token: str,
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    records: list[dict[str, Any]] = []
    offset: str | None = None

    while True:
        params: list[tuple[str, str]] = [("pageSize", "100")]
        if offset:
            params.append(("offset", offset))
        if fields:
            for field in fields:
                if field:
                    params.append(("fields[]", field))

        url = f"{airtable_table_url(base_id, table_name)}?{urlencode(params)}"
        data = http_json("GET", url, headers)
        batch = data.get("records", [])
        if isinstance(batch, list):
            records.extend(batch)
        offset = data.get("offset")
        if not offset:
            break

    return records


def airtable_patch_record(
    base_id: str,
    table_name: str,
    token: str,
    record_id: str,
    fields: dict[str, Any],
) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{airtable_table_url(base_id, table_name)}/{record_id}"
    http_json("PATCH", url, headers, {"fields": fields})


def airtable_find_by_url(
    base_id: str,
    table_name: str,
    token: str,
    url_field: str,
    issue_url: str,
) -> dict[str, Any] | None:
    if not url_field:
        return None

    escaped_url = issue_url.replace("'", "\\'")
    formula = f"{{{url_field}}}='{escaped_url}'"
    params = urlencode({"maxRecords": 1, "filterByFormula": formula})
    url = f"{airtable_table_url(base_id, table_name)}?{params}"
    headers = {"Authorization": f"Bearer {token}"}
    data = http_json("GET", url, headers)
    records = data.get("records", [])
    if records:
        return records[0]
    return None


def github_fetch_issues(
    repo: str, state: str, token: str | None
) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        params = urlencode({"state": state, "per_page": 100, "page": page})
        url = f"https://api.github.com/repos/{repo}/issues?{params}"
        batch = http_json("GET", url, headers)
        if not isinstance(batch, list) or not batch:
            break

        for item in batch:
            # Pull requests appear in /issues endpoint; skip them.
            if "pull_request" not in item:
                issues.append(item)
        page += 1

    return issues


def maybe_set(fields: dict[str, Any], name: str, value: Any) -> None:
    if name:
        fields[name] = value


def infer_github_labels(title: str) -> list[str]:
    lowered = title.lower()
    labels: list[str] = []
    if any(token in lowered for token in ("detector", "acceptance", "register")):
        labels.extend(["research", "detector", "high-priority"])
    elif any(token in lowered for token in ("qiskit", "parity")):
        labels.extend(["qiskit", "verification", "high-priority"])
    elif any(token in lowered for token in ("refactor", "monolith", "decompose")):
        labels.extend(["refactor", "maintainability", "high-priority"])
    else:
        labels.append("enhancement")
    return list(dict.fromkeys(labels))


def create_github_issue(
    repo: str,
    token: str | None,
    title: str,
    body: str,
    labels: list[str],
) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"title": title, "body": body, "labels": labels}
    url = f"https://api.github.com/repos/{repo}/issues"
    return github_api_json("POST", url, headers, payload)


def get_github_issue(repo: str, token: str | None, issue_number: int) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    return github_api_json("GET", url, headers)


def triage_github_issue(
    repo: str,
    token: str | None,
    issue_number: int,
    title: str,
) -> None:
    labels = infer_github_labels(title)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    existing_issue = get_github_issue(repo, token, issue_number)
    existing_labels = [item.get("name", "") for item in existing_issue.get("labels", [])]
    missing_labels = [label for label in labels if label not in existing_labels]
    if missing_labels:
        github_api_json(
            "POST",
            f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels",
            headers,
            {"labels": missing_labels},
        )

    comment_body = (
        "Tracked from the Airtable board and flagged for backlog triage. "
        "The project’s current blocker path is detector semantics and parity verification, "
        "so this item should be treated as a priority ticket until it is explicitly closed."
    )
    github_api_json(
        "POST",
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        headers,
        {"body": comment_body},
    )


def issue_to_airtable_fields(
    issue: dict[str, Any], repo: str
) -> tuple[str, dict[str, Any]]:
    issue_num_field = field_name("AIRTABLE_FIELD_ISSUE_NUMBER", "Issue Number")
    title_field = field_name("AIRTABLE_FIELD_TITLE", "Title")
    status_field = field_name("AIRTABLE_FIELD_STATUS", "Status")
    url_field = field_name("AIRTABLE_FIELD_URL", "URL")
    labels_field = field_name("AIRTABLE_FIELD_LABELS", "Labels")
    assignees_field = field_name("AIRTABLE_FIELD_ASSIGNEES", "Assignees")
    milestone_field = field_name("AIRTABLE_FIELD_MILESTONE", "Milestone")
    state_field = field_name("AIRTABLE_FIELD_STATE", "State")
    repo_field = field_name("AIRTABLE_FIELD_REPOSITORY", "Repository")
    created_at_field = field_name("AIRTABLE_FIELD_CREATED_AT", "Created At")
    updated_at_field = field_name("AIRTABLE_FIELD_UPDATED_AT", "Updated At")
    synced_at_field = field_name("AIRTABLE_FIELD_SYNCED_AT", "Synced At")

    if not issue_num_field:
        raise RuntimeError("AIRTABLE_FIELD_ISSUE_NUMBER cannot be empty")
    if not title_field:
        raise RuntimeError("AIRTABLE_FIELD_TITLE cannot be empty")

    issue_number = int(issue["number"])
    issue_state = issue.get("state", "open")
    status_open = os.getenv("AIRTABLE_STATUS_OPEN", "Todo").strip() or "Todo"
    status_closed = os.getenv("AIRTABLE_STATUS_CLOSED", "Done").strip() or "Done"
    status = status_closed if issue_state == "closed" else status_open

    label_names = ", ".join(label.get("name", "") for label in issue.get("labels", []))
    assignees = ", ".join(a.get("login", "") for a in issue.get("assignees", []))
    milestone = (issue.get("milestone") or {}).get("title", "")

    fields: dict[str, Any] = {}
    maybe_set(fields, issue_num_field, issue_number)
    maybe_set(fields, title_field, issue.get("title", ""))
    maybe_set(fields, status_field, status)
    maybe_set(fields, url_field, issue.get("html_url", ""))
    maybe_set(fields, labels_field, label_names)
    maybe_set(fields, assignees_field, assignees)
    maybe_set(fields, milestone_field, milestone)
    maybe_set(fields, state_field, issue_state)
    maybe_set(fields, repo_field, repo)
    maybe_set(fields, created_at_field, issue.get("created_at", ""))
    maybe_set(fields, updated_at_field, issue.get("updated_at", ""))
    maybe_set(fields, synced_at_field, datetime.now(timezone.utc).isoformat())

    return issue_num_field, fields


def issue_created_key(issue: dict[str, Any]) -> str:
    return str(issue.get("created_at", ""))


def record_created_key(record: dict[str, Any]) -> str:
    return str(record.get("createdTime", ""))


def reconcile_existing_records_by_creation_order(
    base_id: str,
    table_name: str,
    token: str,
    issues: list[dict[str, Any]],
    issue_number_field: str,
    title_field: str,
    url_field: str,
    issue_fields_by_number: dict[int, dict[str, Any]],
) -> int:
    tracked_fields = [issue_number_field, title_field]
    if url_field:
        tracked_fields.append(url_field)

    records = airtable_list_records(
        base_id=base_id,
        table_name=table_name,
        token=token,
        fields=tracked_fields,
    )

    by_issue_number: dict[int, dict[str, Any]] = {}
    by_url: dict[str, dict[str, Any]] = {}
    for record in records:
        record_fields = record.get("fields", {})
        number_raw = record_fields.get(issue_number_field)
        if isinstance(number_raw, (int, float)):
            by_issue_number[int(number_raw)] = record
        elif isinstance(number_raw, str) and number_raw.strip().isdigit():
            by_issue_number[int(number_raw.strip())] = record

        if url_field:
            url_value = record_fields.get(url_field)
            if isinstance(url_value, str) and url_value.strip():
                by_url[url_value.strip()] = record

    unassigned_records: list[dict[str, Any]] = []
    for record in records:
        record_fields = record.get("fields", {})
        number_raw = record_fields.get(issue_number_field)
        has_number = False
        if isinstance(number_raw, (int, float)):
            has_number = True
        elif isinstance(number_raw, str) and number_raw.strip().isdigit():
            has_number = True
        if not has_number:
            unassigned_records.append(record)

    unassigned_records.sort(key=record_created_key)

    sorted_issues = sorted(issues, key=issue_created_key)
    unmatched_issue_numbers: list[int] = []
    for issue in sorted_issues:
        number = int(issue["number"])
        issue_url = str(issue.get("html_url", "")).strip()
        if number in by_issue_number:
            continue
        if issue_url and issue_url in by_url:
            rec = by_url[issue_url]
            patch_fields = issue_fields_by_number[number]
            airtable_patch_record(
                base_id=base_id,
                table_name=table_name,
                token=token,
                record_id=rec["id"],
                fields=patch_fields,
            )
            by_issue_number[number] = rec
            continue
        unmatched_issue_numbers.append(number)

    backfilled = 0
    for record, number in zip(unassigned_records, unmatched_issue_numbers):
        patch_fields = issue_fields_by_number[number]
        airtable_patch_record(
            base_id=base_id,
            table_name=table_name,
            token=token,
            record_id=record["id"],
            fields=patch_fields,
        )
        backfilled += 1

    return backfilled


def upsert_issue_record(
    base_id: str,
    table_name: str,
    token: str,
    issue_field: str,
    issue_number: int,
    fields: dict[str, Any],
) -> str:
    existing = airtable_find_by_issue_number(
        base_id=base_id,
        table_name=table_name,
        token=token,
        issue_field=issue_field,
        issue_number=issue_number,
    )

    if existing:
        airtable_patch_record(
            base_id=base_id,
            table_name=table_name,
            token=token,
            record_id=existing["id"],
            fields=fields,
        )
        return "updated"

    url_field = field_name("AIRTABLE_FIELD_URL", "URL")
    issue_url = fields.get(url_field, "") if url_field else ""
    if isinstance(issue_url, str) and issue_url.strip() and url_field:
        existing_by_url = airtable_find_by_url(
            base_id=base_id,
            table_name=table_name,
            token=token,
            url_field=url_field,
            issue_url=issue_url.strip(),
        )
        if existing_by_url:
            airtable_patch_record(
                base_id=base_id,
                table_name=table_name,
                token=token,
                record_id=existing_by_url["id"],
                fields=fields,
            )
            return "updated"

    url = airtable_table_url(base_id, table_name)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    http_json("POST", url, headers, {"fields": fields})
    return "created"


def main() -> None:
    airtable_token = require_env("AIRTABLE_TOKEN")
    airtable_base = require_env("AIRTABLE_BASE_ID")
    airtable_table = require_env("AIRTABLE_TABLE_NAME")

    github_repo = require_env("GITHUB_REPOSITORY")
    github_token = os.getenv("GITHUB_TOKEN", "").strip() or None
    state = os.getenv("AIRTABLE_SYNC_STATE", "all").strip().lower()
    if state not in {"open", "closed", "all"}:
        raise SystemExit("AIRTABLE_SYNC_STATE must be one of: open, closed, all")

    issues = github_fetch_issues(github_repo, state, github_token)
    issues = sorted(issues, key=issue_created_key)

    issue_field_name = field_name("AIRTABLE_FIELD_ISSUE_NUMBER", "Issue Number")
    title_field_name = field_name("AIRTABLE_FIELD_TITLE", "Title")
    url_field_name = field_name("AIRTABLE_FIELD_URL", "URL")
    status_field_name = field_name("AIRTABLE_FIELD_STATUS", "Status")

    issue_fields_by_number: dict[int, dict[str, Any]] = {}
    for issue in issues:
        _, fields = issue_to_airtable_fields(issue, github_repo)
        issue_fields_by_number[int(issue["number"])] = fields

    backfilled = reconcile_existing_records_by_creation_order(
        base_id=airtable_base,
        table_name=airtable_table,
        token=airtable_token,
        issues=issues,
        issue_number_field=issue_field_name,
        title_field=title_field_name,
        url_field=url_field_name,
        issue_fields_by_number=issue_fields_by_number,
    )

    created = 0
    updated = 0
    created_from_airtable = 0
    triaged_from_airtable = 0

    for issue in issues:
        issue_field, fields = issue_to_airtable_fields(issue, github_repo)
        number = int(issue["number"])
        action = upsert_issue_record(
            base_id=airtable_base,
            table_name=airtable_table,
            token=airtable_token,
            issue_field=issue_field,
            issue_number=number,
            fields=fields,
        )
        if action == "created":
            created += 1
        else:
            updated += 1

    records = airtable_list_records(
        base_id=airtable_base,
        table_name=airtable_table,
        token=airtable_token,
        fields=[issue_field_name, title_field_name, url_field_name, status_field_name],
    )

    for record in records:
        record_fields = record.get("fields", {})
        issue_number_value = record_fields.get(issue_field_name)
        title_value = record_fields.get(title_field_name, "")
        status_value = record_fields.get(status_field_name, "")
        if not isinstance(title_value, str):
            title_value = str(title_value or "")

        if issue_number_value in (None, ""):
            if not title_value.strip():
                continue
            issue_body = (
                "Imported from the Airtable board for backlog triage. "
                "This ticket did not have a GitHub issue number yet, so it has been created as a new issue."
            )
            issue = create_github_issue(
                github_repo,
                github_token,
                title_value.strip(),
                issue_body,
                infer_github_labels(title_value.strip()),
            )
            number = int(issue["number"])
            patch_fields: dict[str, Any] = {}
            maybe_set(patch_fields, issue_field_name, number)
            maybe_set(patch_fields, title_field_name, title_value.strip())
            maybe_set(patch_fields, url_field_name, issue.get("html_url", ""))
            airtable_patch_record(
                base_id=airtable_base,
                table_name=airtable_table,
                token=airtable_token,
                record_id=record["id"],
                fields=patch_fields,
            )
            created_from_airtable += 1
            continue

        if isinstance(issue_number_value, (float, int)):
            numeric_value = int(issue_number_value)
        elif isinstance(issue_number_value, str) and issue_number_value.strip().isdigit():
            numeric_value = int(issue_number_value.strip())
        else:
            continue

        if not isinstance(status_value, str) or not status_value.strip():
            triage_github_issue(github_repo, github_token, numeric_value, title_value.strip() or f"Issue #{numeric_value}")
            triaged_from_airtable += 1

    print(
        json.dumps(
            {
                "repository": github_repo,
                "issues_synced": len(issues),
                "records_created": created,
                "records_updated": updated,
                "records_backfilled_by_creation_order": backfilled,
                "airtable_rows_created_as_github_issues": created_from_airtable,
                "airtable_rows_triaged": triaged_from_airtable,
                "airtable_base": airtable_base,
                "airtable_table": airtable_table,
                "state_filter": state,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
