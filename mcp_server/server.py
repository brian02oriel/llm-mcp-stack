import os
import sqlite3
from contextlib import closing

from mcp.server.mcpserver import MCPServer

DB_PATH = os.getenv("KPI_DB", "kpi.db")

mcp = MCPServer("kpi-tools")


def query(sql: str, params: tuple = ()) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        return conn.execute(sql, params).fetchall()


@mcp.tool()
def list_regions() -> str:
    """List every region that has revenue data available.

    Call this first when the user mentions a region you are unsure about,
    or asks what data exists.
    """
    rows = query("SELECT DISTINCT region FROM revenue ORDER BY region")
    return ", ".join(r[0] for r in rows)


@mcp.tool()
def revenue_by_quarter(year: int, quarter: int, region: str | None = None) -> str:
    """Total revenue for one fiscal quarter, optionally filtered to a region.

    Args:
        year: Four-digit fiscal year, e.g. 2024.
        quarter: Quarter number, 1 through 4.
        region: Optional region code such as EMEA or LATAM. Omit for all regions.
    """
    if quarter not in (1, 2, 3, 4):
        return "Error: quarter must be 1, 2, 3 or 4."

    sql = "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE year = ? AND quarter = ?"
    params: tuple = (year, quarter)
    if region:
        sql += " AND region = ?"
        params += (region.upper(),)

    total = query(sql, params)[0][0]
    if total == 0:
        return f"No revenue data found for {year} Q{quarter}" + (f" in {region}." if region else ".")
    scope = region.upper() if region else "all regions"
    return f"{year} Q{quarter} revenue ({scope}): {total:,.2f} EUR"


@mcp.tool()
def growth_rate(year_a: int, quarter_a: int, year_b: int, quarter_b: int) -> str:
    """Percentage growth in total revenue from period A to period B.

    Use this instead of calling revenue_by_quarter twice and doing the arithmetic
    yourself — this returns an exact computed figure.
    """
    def total(y: int, q: int) -> float:
        return query(
            "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE year = ? AND quarter = ?",
            (y, q),
        )[0][0]

    a, b = total(year_a, quarter_a), total(year_b, quarter_b)
    if a == 0:
        return f"No baseline data for {year_a} Q{quarter_a}; cannot compute growth."
    return (
        f"{year_a} Q{quarter_a} → {year_b} Q{quarter_b}: "
        f"{((b - a) / a) * 100:+.2f}% ({a:,.0f} → {b:,.0f} EUR)"
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",   # serves POST /mcp
        host="0.0.0.0",
        port=9000,
        stateless_http=True,   # no session state — required for multi-replica scaling
        json_response=True,    # plain JSON instead of SSE framing; simpler to debug
    )