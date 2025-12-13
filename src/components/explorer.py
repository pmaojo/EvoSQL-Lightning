from src.utils.db_connect import get_schema_details, get_table_sample
from src.semantic_catalog.profiling import profile_column
from src.semantic_catalog.store import SemanticStore

class SchemaDiscovery:
    def __init__(self):
        self.has_run = False
        # Initialize store here (lazy init might be better in real apps depending on pickling)
        self.store = SemanticStore()

    def run(self, db_url=None):
        if not db_url:
            print("No DB URL provided. Skipping discovery.")
            return

        print(f"Starting Schema Discovery for {db_url}...")
        
        # 1. Introspection
        schema = get_schema_details(db_url)
        print(f"Found {len(schema)} tables.")
        
        metadata_batch = []
        graph_hints = {}
        
        for table_name, details in schema.items():
            # Refinement 4: Extract Graph Hints (FKs)
            # details['foreign_keys'] is list of dicts from SQLAlchemy introspection
            if details['foreign_keys']:
                hints = []
                for fk in details['foreign_keys']:
                    # Simple hint string: "Table A matches Table B on A.col = B.col"
                    referred_table = fk.get('referred_table')
                    constrained_cols = fk.get('constrained_columns', [])
                    referred_cols = fk.get('referred_columns', []) # Note: referred_columns might not be always available depending on driver
                    
                    if referred_table and constrained_cols:
                        cols_str = ", ".join(constrained_cols)
                        # We assume simplistic single-col FK for the text description for now
                        hint_text = f"JOIN HINT: Table '{table_name}' joins with '{referred_table}' on {table_name}.{constrained_cols[0]} = {referred_table}.id (Verify exact PK)"
                        hints.append(hint_text)
                
                if hints:
                    graph_hints[table_name] = hints

            # Get a sample for profiling this table
            sample_rows = get_table_sample(db_url, table_name, limit=20)
            
            # 2. Profiling & Enrichment
            for col in details['columns']:
                col_name = col['name']
                # Extract column values from sample rows
                col_values = [row.get(col_name) for row in sample_rows if row.get(col_name) is not None]
                profile = profile_column(col_values)
                
                # Create a rich description for the vector store
                # Improvement: Include FK info if available
                description = (
                    f"Table: {table_name}, Column: {col_name}. "
                    f"Type: {col['type']} (Inferred: {profile['inferred_type']}). "
                    f"Cardinality: {profile['cardinality']}. "
                    f"Sample values: {', '.join(map(str, profile['sample_values']))}."
                )
                
                doc_id = f"{table_name}.{col_name}"
                metadata = {
                    "table": table_name,
                    "column": col_name,
                    "sql_type": col['type'],
                    "inferred_type": profile['inferred_type'],
                    "is_pk": str(col['primary_key'])
                }
                
                metadata_batch.append({
                    "id": doc_id,
                    "text": description,
                    "metadata": metadata
                })
                
        # 3. Indexing
        if metadata_batch:
            print(f"Indexing {len(metadata_batch)} schema elements to Semantic Store...")
            self.store.add_schema_metadata(metadata_batch)
            print("Indexing complete.")
        else:
            print("No schema elements to index.")
            
        # 4. Store Graph Hints
        if graph_hints:
            print(f"Storing {len(graph_hints)} graph/join hints...")
            self.store.add_graph_hints(graph_hints)

        
        self.has_run = True
        print("Schema Discovery complete.")

