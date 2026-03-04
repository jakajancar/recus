static:
    uv run ruff check
    uv run pyright

api-docs:
    npx @redocly/cli@latest lint docs/openapi.yaml --config docs/redocly.yaml
    npx @redocly/cli@latest build-docs docs/openapi.yaml --config docs/redocly.yaml -o docs/api.html

test-api-docs:
    uv run pytest tests/test_api.py -v
