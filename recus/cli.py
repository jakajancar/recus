from __future__ import annotations

import getpass

from typing import Annotated

from cyclopts import App, Parameter

from recus.account_resolver import AccountResolver
from recus.avails import search as avails_search
from recus.booking import app as booking_app
from recus import cli_groups
from recus.client import AnonClient, AuthClient
from recus.output import pretty, table
from recus.state import user_state

app = App(
    name="recus",
    help="CLI for the rec.us reservation API.",
    version="0.1.0",
    # do not parse these as they are injected via meta-app
    default_parameter=Parameter(parse="^(?!(account|account_resolver)$)"),
    group_commands=cli_groups.commands,
    group_parameters=cli_groups.params,
)

@app.meta.default
def launcher(
    *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    explicit_account: Annotated[str | None, Parameter(name="--account", show=True, help="Account to use for authenticated requests (if multiple logged in).")] = None,
) -> None:
    additional_kwargs = {}
    command, bound, ignored = app.parse_args(tokens)
    account_resolver = AccountResolver(explicit_value=explicit_account)
    if "account_resolver" in ignored:
        additional_kwargs["account_resolver"] = account_resolver
    if "account" in ignored:
        additional_kwargs["account"] = account_resolver.required()
    return command(*bound.args, **bound.kwargs, **additional_kwargs)

app.command(avails_search, name="avails", group=cli_groups.anon)
app.command(booking_app)

@app.command(group=cli_groups.auth)
def login(*, account_resolver: AccountResolver) -> None:
    """Log in with an Rec.us email and password."""

    # Read username
    suggested_account = account_resolver.optional() or ""
    explicit_account = input(f"Email [{suggested_account}]: ")
    account = explicit_account or suggested_account
    if not account:
        raise SystemExit("Account email must be provided.")

    # Read password
    password = getpass.getpass("Password: ")

    client = AuthClient(account)
    client.login(password)
    print(f"Logged in as {account}")


@app.command(group=cli_groups.auth)
def logout(*, account: str) -> None:
    """Log out and remove a stored account."""
    with user_state() as state:
        if account not in state.accounts:
            raise SystemExit(f"No account for {account}")
        del state.accounts[account]
    print(f"Removed {account}")


@app.command(group=cli_groups.auth)
def accounts() -> None:
    """List stored accounts and token status."""
    with user_state() as state:
        tokens = list(state.accounts.values())
    if not tokens:
        print("No accounts stored.")
        return

    rows = []
    for token in tokens:
        client = AuthClient(token.email)
        try:
            client.get("/v1/users/me")
            status = "ok"
        except Exception:
            status = "failed"
        rows.append((token.email, status))

    table(["email", "status"], rows)


@app.command(group=cli_groups.anon)
def orgs() -> None:
    """List organizations."""
    all_orgs = AnonClient().get_all("/v1/organizations")
    table(
        ["slug", "name"],
        [(o["slug"], o.get("displayName") or o["name"]) for o in all_orgs],
    )


@app.command(group=cli_groups.anon)
def regions() -> None:
    """List all geographic regions."""
    data = AnonClient().get("/v1/regions")
    table(["id", "name"], [(r["id"], r["name"]) for r in data])


@app.command(group=cli_groups.http)
def get(path: str, /, *, account_resolver: AccountResolver, auth: bool = False) -> None:
    """GET any API path and pretty-print the JSON response.

    --auth: send authentication header.
    """
    client = AuthClient(account_resolver.required()) if auth else AnonClient()
    data = client.get(path)
    pretty(data)



def main() -> None:
    app.meta()

if __name__ == "__main__":
    main()
