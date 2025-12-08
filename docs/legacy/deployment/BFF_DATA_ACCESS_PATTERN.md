# BFF Data Access Pattern

**Version**: 1.0
**Date**: 2025-11-11
**Status**: ✅ Canonical

## Principle

All substrate-api BFF (Backend-for-Frontend) routes follow a **unified data access pattern** with direct SQL queries. This ensures consistency, performance, and pgbouncer compatibility.

## Pattern Architecture

### 1. Authentication Layer
- **Middleware**: `AuthMiddleware` verifies JWT tokens
- **Dependency**: Routes use `user: dict = Depends(verify_jwt)`
- **Result**: Sets `request.state.user_id` for authorization

### 2. Data Access Layer
- **Database**: Direct SQL via `db=Depends(get_db)`
- **Connection**: Configured with `statement_cache_size=0` for pgbouncer
- **Pattern**: Bypasses RLS, uses explicit workspace filtering

### 3. Authorization Layer
- **Workspace Isolation**: Filter by `workspace_id` in SQL WHERE clauses
- **Derivation**: `workspace_id = get_or_create_workspace(user["user_id"])`
- **Enforcement**: Application-level data isolation

## Canonical Example

```python
@router.get("/baskets/{basket_id}/blocks")
async def list_blocks(
    basket_id: str,
    user: dict = Depends(verify_jwt),  # Auth
    db=Depends(get_db),  # Data access
):
    """BFF pattern: Direct SQL with explicit workspace filtering."""
    workspace_id = get_or_create_workspace(user["user_id"])

    query = """
        SELECT id, title, content, semantic_type
        FROM blocks
        WHERE basket_id = :basket_id
        AND workspace_id = :workspace_id  -- Authorization
        ORDER BY created_at DESC
    """

    results = await db.fetch_all(
        query,
        values={
            "basket_id": basket_id,
            "workspace_id": workspace_id,
        }
    )

    return [dict(row) for row in results]
```

## Anti-Patterns

### ❌ Don't: Use Supabase Client in BFF Routes

**Wrong**:
```python
# Anti-pattern: Supabase client enforces RLS (designed for frontend)
@router.get("/blocks")
def list_blocks(user: dict = Depends(verify_jwt)):
    resp = supabase.table("blocks").select("*").execute()  # ❌
    return resp.data
```

**Problems**:
- Enforces RLS (designed for untrusted clients, not service-to-service)
- Causes "permission denied for schema public" errors
- Inconsistent with direct SQL pattern
- Creates maintenance burden

### ❌ Don't: Rely on RLS for BFF Authorization

**Wrong**:
```python
# Anti-pattern: Depending on RLS policies
@router.get("/blocks")
def list_blocks(user: dict = Depends(verify_jwt)):
    # Assumes RLS will filter by workspace - implicit, fragile
    query = "SELECT * FROM blocks"  # ❌
    return await db.fetch_all(query)
```

**Problems**:
- Implicit authorization (RLS configuration elsewhere)
- Hard to audit and debug
- Requires complex RLS policy setup
- Breaks with service credentials

### ❌ Don't: Mix Data Access Patterns

**Wrong**:
```python
# Anti-pattern: Inconsistent patterns across routes
@router.get("/baskets")
async def get_baskets(db=Depends(get_db)):
    return await db.fetch_all("SELECT * FROM baskets")  # ✅ Direct SQL

@router.get("/blocks")
def get_blocks(user: dict = Depends(verify_jwt)):
    return supabase.table("blocks").select("*").execute().data  # ❌ Supabase client
```

**Problems**:
- Team confusion about which pattern to use
- Different failure modes per pattern
- Maintenance burden (two codepaths to maintain)

## When to Use Supabase Client

✅ **Frontend Routes** (Next.js client components)
- User's browser makes direct requests to Supabase
- RLS provides row-level security
- Client authenticated with user JWT

✅ **Admin Operations** (backend with service role key)
- Use `supabase_admin_client` for privileged operations
- Explicitly bypasses RLS by design
- Rare use case (migrations, admin tools)

## Infrastructure Configuration

### Pgbouncer Compatibility

Supabase uses pgbouncer in transaction pooling mode. Direct SQL requires:

```python
# In deps.py - automatically configured
database_url += "?statement_cache_size=0&prepared_statement_cache_size=0"
```

**Why**: Pgbouncer transaction mode doesn't support prepared statements. Disabling caching prevents `DuplicatePreparedStatementError`.

### Connection Management

- **Global instance**: Single `Database` instance per application
- **Thread-safe**: Uses asyncio lock for initialization
- **Lifecycle**: Connect on first use, disconnect on shutdown

## Migration from Legacy Patterns

If you find routes using Supabase client:

1. **Add dependencies**: `db=Depends(get_db), user: dict = Depends(verify_jwt)`
2. **Replace client call**: Convert `supabase.table().select()` to direct SQL
3. **Add workspace filter**: Include `WHERE workspace_id = :workspace_id`
4. **Make async**: Change `def` to `async def`, `fetch_all` returns awaitable

**Example Migration**:
```python
# Before (Supabase client)
def list_blocks(basket_id: str, user: dict = Depends(verify_jwt)):
    workspace_id = get_or_create_workspace(user["user_id"])
    resp = supabase.table("blocks")\
        .select("*")\
        .eq("basket_id", basket_id)\
        .eq("workspace_id", workspace_id)\
        .execute()
    return resp.data

# After (Direct SQL)
async def list_blocks(
    basket_id: str,
    user: dict = Depends(verify_jwt),
    db=Depends(get_db),
):
    workspace_id = get_or_create_workspace(user["user_id"])
    query = """
        SELECT * FROM blocks
        WHERE basket_id = :basket_id
        AND workspace_id = :workspace_id
    """
    results = await db.fetch_all(
        query,
        values={"basket_id": basket_id, "workspace_id": workspace_id}
    )
    return [dict(row) for row in results]
```

## See Also

- [YARNNN Architecture Canon](YARNNN_ARCHITECTURE_CANON.md) - Overall system architecture
- [Service-to-Service Auth](SERVICE_TO_SERVICE_AUTH.md) - JWT verification patterns
- Commit `7c554b75` - Blocks endpoint migration from Supabase client to direct SQL
- Commit `96579ba9` - Pgbouncer compatibility fix
