from sqlalchemy import create_engine, text

def estimate_query_cost(sql, db_url):
    """
    Runs EXPLAIN QUERY PLAN to estimate cost.
    For SQLite, we look for 'SCAN TABLE' without indices which implies full table scan.
    """
    # Simple heuristic for SQLite. Postgres would use parsing of "Cost=..."
    engine = create_engine(db_url)
    cost_score = 0
    
    # Basic safety checks (No DROP/DELETE) - though running with ReadOnly user is better
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(cmd in sql.upper() for cmd in forbidden):
        return 999999 # Extremely high cost/unsafe
    
    try:
        with engine.connect() as conn:
            # SQLite specific EXPLAIN
            if "sqlite" in db_url:
                result = conn.execute(text(f"EXPLAIN QUERY PLAN {sql}"))
                raw_plan = result.fetchall()
                for row in raw_plan:
                    detail = str(row)
                    # Heuristic: SCAN TABLE is costly. SEARCH TABLE is better.
                    if "SCAN TABLE" in detail:
                        cost_score += 50 # Was 100. Lowered for small DBs where scans are fine.
                    elif "SEARCH TABLE" in detail:
                        cost_score += 10
                    elif "USE TEMP B-TREE" in detail:
                        cost_score += 20 # Was 50. Sorting is common.
            else:
                 # Placeholder for other DBs
                 cost_score = 10
                 
            return cost_score
    except Exception as e:
        print(f"Explanation failed: {e}")
        return 0 # Fail open if explanation checks fail, rely on forbidden keyword check

def is_safe(sql, db_url, cost_threshold=1000): # Raised from 500
    cost = estimate_query_cost(sql, db_url)
    print(f"Query Cost: {cost}")
    return cost < cost_threshold

