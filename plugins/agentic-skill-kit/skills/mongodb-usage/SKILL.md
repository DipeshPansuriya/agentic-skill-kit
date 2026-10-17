---
name: mongodb-usage
description: "Read-only MongoDB exploration through a MongoDB MCP server (mcp__mongodb__* tools) — list databases and collections, inspect schemas and indexes, query and aggregate records. Use when the user asks to query MongoDB, show collections, get a collection schema, list databases, search records or check indexes, and a MongoDB MCP server is configured in .mcp.json."
---

# MongoDB MCP Usage

> **Prerequisite — requires a MongoDB MCP server in `.mcp.json`.** None is configured in this hub by default,
> so the `mcp__mongodb__*` tools below will not exist until one is added (for example the official
> `mongodb-mcp-server`, connection string supplied via an environment variable, read-only mode on).
> **Without it**, do not pretend to call these tools: say the server is missing, and fall back to `mongosh`
> run by the user (or an allowed `Bash(mongosh:*)` command) with read-only queries, or to static analysis of the
> code's queries. For schema design questions use `agentic-skill-kit:database-engineering`; for query syntax use
> `agentic-skill-kit:database-engineering`.

Use the MongoDB MCP server to integrate database queries into workflows.

## Read-Only Access

MongoDB MCP is configured in read-only mode. Only queries and data retrieval are supported. No write, update, or delete operations.

## Database Queries

Use `mcp__mongodb__*` tools for:

- Listing databases
- Viewing collection schemas
- Querying collection data
- Analyzing indexes

## Integration Pattern

Tool names depend on the server; check the tool list the session actually exposes. The official
`mongodb-mcp-server` uses names such as `list-databases`, `list-collections`, `collection-schema`,
`collection-indexes`, `find`, `aggregate` and `count` (prefixed `mcp__mongodb__` when the server is named `mongodb`).

1. List available databases
2. Explore collections
3. Get schema information
4. Query data as needed for analysis (projection + limit; never dump whole collections)
5. Format results for user consumption

## Environment Variables

The MCP server needs a connection string (for the official server, `MDB_MCP_CONNECTION_STRING`; check the
server's README). Store it in the OS environment / secret store and reference it as `${VAR}` in `.mcp.json` —
never as a literal. Use a database user with read-only roles.

## Cost Considerations

- Minimize database calls when possible
- Use schema queries before running analysis queries
- Cache results locally if multiple calls needed
- Prefer aggregation pipelines for complex operations
