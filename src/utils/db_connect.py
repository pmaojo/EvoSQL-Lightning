from sqlalchemy import create_engine, inspect, text

def get_inspector(db_url):
    engine = create_engine(db_url)
    return inspect(engine)

def get_schema_details(db_url):
    """
    Introspects the database and returns a rich dictionary of the schema.
    Structure:
    {
        "table_name": {
            "columns": [{"name": "col1", "type": "INTEGER", "primary_key": True}, ...],
            "foreign_keys": [{"constrained_columns": ["user_id"], "referred_table": "users", ...}]
        },
        ...
    }
    """
    inspector = get_inspector(db_url)
    schema_info = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        pk_constraint = inspector.get_pk_constraint(table_name)
        pks = pk_constraint.get('constrained_columns', []) if pk_constraint else []
        
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col['name'],
                "type": str(col['type']),
                "primary_key": col['name'] in pks,
                "nullable": col.get('nullable', True)
            })
            
        fks = inspector.get_foreign_keys(table_name)
        
        schema_info[table_name] = {
            "columns": columns,
            "foreign_keys": fks
        }
        
    return schema_info

def get_table_sample(db_url, table_name, limit=5):
    """Returns a sample of rows from a table."""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        try:
            # Use text() for safe SQL execution, mostly consistent across dialects for simple SELECT
            query = text(f"SELECT * FROM {table_name} LIMIT :limit")
            result = conn.execute(query, {"limit": limit})
            return [dict(row._mapping) for row in result]
        except Exception as e:
            print(f"Error sampling table {table_name}: {e}")
            return []

