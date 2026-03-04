from __future__ import annotations

from cyclopts import Group

auth = Group.create_ordered("Authentication")
anon = Group.create_ordered("Anonymous operations")
authd = Group.create_ordered("Authenticated operations")
http = Group.create_ordered("HTTP low-level operations")
commands = Group.create_ordered("Commands")
params = Group.create_ordered("Parameters")
