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


def field_name(env_name: str, default: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


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


def upsert_issue_record(
    base_id: str,
    table_name: str,
    token: str,
    issue_field: str,
    issue_number: int,
    fields: dict[str, Any],
) -> str:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    existing = airtable_find_by_issue_number(
        base_id=base_id,
        table_name=table_name,
        token=token,
        issue_field=issue_field,
        issue_number=issue_number,
    )

    if existing:
        rec_id = existing["id"]
        url = f"{airtable_table_url(base_id, table_name)}/{rec_id}"
        http_json("PATCH", url, headers, {"fields": fields})
        return "updated"

    url = airtable_table_url(base_id, table_name)
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
    created = 0
    updated = 0

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

    print(
        json.dumps(
            {
                "repository": github_repo,
                "issues_synced": len(issues),
                "records_created": created,
                "records_updated": updated,
                "airtable_base": airtable_base,
                "airtable_table": airtable_table,
                "state_filter": state,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
