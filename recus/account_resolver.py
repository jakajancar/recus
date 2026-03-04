from dataclasses import dataclass

from recus.state import user_state

@dataclass
class AccountResolver:
    explicit_value: str | None

    def required(self) -> str:
        if self.explicit_value:
            return self.explicit_value
        with user_state() as state:
            if not state.accounts:
                raise SystemExit("No accounts stored. Run: recus login")
            if len(state.accounts) == 1:
                return next(iter(state.accounts))
            emails = ", ".join(state.accounts)
            raise SystemExit(f"Multiple accounts stored ({emails}). Use --account.")

    def optional(self) -> str | None:
        if self.explicit_value:
            return self.explicit_value
        with user_state() as state:
            if len(state.accounts) == 1:
                return next(iter(state.accounts))
            return None
