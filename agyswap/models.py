from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Account:
    number: int
    email: str
    disabled: bool = False
    alias: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class SequenceData:
    active_email: Optional[str] = None
    sequence: list[int] = field(default_factory=list)
    accounts: dict[int, Account] = field(default_factory=dict)
    last_updated: str = field(default_factory=now_iso)

    def to_dict(self) -> dict:
        return {
            "activeEmail": self.active_email,
            "lastUpdated": self.last_updated,
            "sequence": self.sequence,
            "accounts": {
                str(num): {
                    "email": acc.email,
                    "disabled": acc.disabled,
                    "alias": acc.alias,
                    "createdAt": acc.created_at,
                    "updatedAt": acc.updated_at,
                }
                for num, acc in self.accounts.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SequenceData":
        accounts = {}
        for num_str, acc_data in data.get("accounts", {}).items():
            num = int(num_str)
            accounts[num] = Account(
                number=num,
                email=acc_data.get("email", ""),
                disabled=acc_data.get("disabled", False),
                alias=acc_data.get("alias"),
                created_at=acc_data.get("createdAt", ""),
                updated_at=acc_data.get("updatedAt", ""),
            )
        return cls(
            active_email=data.get("activeEmail"),
            sequence=data.get("sequence", []),
            accounts=accounts,
            last_updated=data.get("lastUpdated", ""),
        )
