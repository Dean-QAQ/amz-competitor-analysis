"""Account pool: healthy / softbanned rotation (test with one account)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Account:
    id: str
    label: str = ""
    sites: list[str] = field(default_factory=lambda: ["com"])
    storage_state: str = ""
    profile_dir: str = ""
    enabled: bool = True
    # healthy | softbanned | needs_login | expired | disabled
    status: str = "healthy"
    notes: str = ""
    last_error: str = ""
    last_used_at: str = ""

    def storage_path(self, root: Path) -> Path:
        rel = self.storage_state or f"accounts/storage/{self.id}.json"
        path = Path(rel)
        return path if path.is_absolute() else root / path

    def profile_path(self, root: Path, site: str = "com") -> Path:
        # Always use ASCII home profiles for Chrome on Windows.
        from .browser import profile_dir_for

        path = profile_dir_for(self.id, root, site)
        self.profile_dir = str(path)
        return path

    def supports_site(self, site: str) -> bool:
        return site in self.sites or "*" in self.sites


def _account_from_dict(item: dict[str, Any]) -> Account:
    allowed = {f.name for f in fields(Account)}
    return Account(**{k: v for k, v in item.items() if k in allowed})


@dataclass
class AccountPool:
    path: Path
    accounts: list[Account]
    root: Path

    @classmethod
    def load(cls, path: Path, *, root: Path | None = None) -> "AccountPool":
        path = Path(path)
        root = root or path.parent.parent
        if not path.exists():
            raise FileNotFoundError(
                f"Account pool not found: {path}. Copy accounts/pool.example.json to accounts/pool.json"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        accounts = [_account_from_dict(item) for item in data.get("accounts", [])]
        return cls(path=path, accounts=accounts, root=root)

    def save(self) -> None:
        payload = {"accounts": [asdict(a) for a in self.accounts]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get(self, account_id: str) -> Account:
        for account in self.accounts:
            if account.id == account_id:
                return account
        raise KeyError(f"Account not found: {account_id}")

    def pick(self, site: str, *, account_id: str | None = None) -> Account:
        if account_id:
            account = self.get(account_id)
            if not account.enabled:
                raise RuntimeError(f"Account disabled: {account_id}")
            if account.status == "softbanned":
                raise RuntimeError(f"Account softbanned: {account_id}")
            if not account.supports_site(site):
                raise RuntimeError(f"Account {account_id} does not support site {site}")
            # Explicit id may be needs_login/expired — caller should re-login first.
            return account

        candidates = [
            a
            for a in self.accounts
            if a.enabled and a.status == "healthy" and a.supports_site(site)
        ]
        if not candidates:
            raise RuntimeError(f"No healthy account available for site={site}")
        candidates.sort(key=lambda a: a.last_used_at or "")
        return candidates[0]

    def mark_used(self, account: Account) -> None:
        account.last_used_at = datetime.now(timezone.utc).isoformat()
        self.save()

    def mark_softbanned(self, account: Account, reason: str) -> None:
        account.status = "softbanned"
        account.last_error = reason
        account.last_used_at = datetime.now(timezone.utc).isoformat()
        self.save()

    def mark_needs_login(self, account: Account, reason: str) -> None:
        account.status = "needs_login"
        account.last_error = reason
        account.last_used_at = datetime.now(timezone.utc).isoformat()
        self.save()

    def mark_expired(self, account: Account, reason: str) -> None:
        # Recoverable session drop — keep enabled so re-login + resume works.
        self.mark_needs_login(account, reason)

    def as_dict(self) -> dict[str, Any]:
        return {"accounts": [asdict(a) for a in self.accounts]}
