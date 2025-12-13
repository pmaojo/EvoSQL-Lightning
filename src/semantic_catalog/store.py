import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
import numpy as np

class SemanticStore:
    def __init__(self, persist_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        # We use a simple default embedding function (all-MiniLM-L6-v2) provided by Chroma/SentenceTransformers
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        self.collection = self.client.get_or_create_collection(
            name="schema_catalog",
            embedding_function=self.ef
        )
        
        # In-memory BM25 index
        self.bm25 = None
        self.doc_registry = [] # Maps index to doc ID/Content
        
        # Refinement 4: Graph/Join Hints
        # Simple in-memory dict for now: {table_name: ["Join hint string..."]}
        self.graph_hints = {}
        
        # Attempt to reload BM25 from existing data
        self._rebuild_bm25()


    def _rebuild_bm25(self):
        """Rebuilds BM25 index from current collection data"""
        existing_data = self.collection.get()
        if existing_data['documents']:
            self.doc_registry = existing_data['ids']
            # Tokenize documents for BM25
            tokenized_corpus = [doc.split(" ") for doc in existing_data['documents']]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None
            self.doc_registry = []

    def add_schema_metadata(self, metadata_list):
        """
        Adds rich schema metadata to the store.
        metadata_list: List of dicts with keys: 'id', 'text', 'metadata'
        """
        ids = [item['id'] for item in metadata_list]
        documents = [item['text'] for item in metadata_list]
        metadatas = [item['metadata'] for item in metadata_list]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        # Rebuild BM25 after addition (naive approach for prototype)
        self._rebuild_bm25()

    def add_graph_hints(self, hints_dict):
        """
        Stores FK relationships/join hints.
        hints_dict: {table_name: ["Hint: Table users joins with orders on id=user_id"]}
        """
        self.graph_hints.update(hints_dict)

    def search(self, query, top_k=5):
        """
        Hybrid Search using RRF (Reciprocal Rank Fusion) + Graph Hints.
        """
        if not self.bm25:
            return []

        # 1. Vector Search
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        # vector_results structure: {'ids': [['id1', ...]], ...}
        
        # 2. Keyword Search (BM25)
        # We need to scan all docs to get scores, then sort
        tokenized_query = query.split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # Get top_k indices
        top_n_indices = np.argsort(bm25_scores)[::-1][:top_k]
        bm25_ids = [self.doc_registry[i] for i in top_n_indices]
        
        # 3. RRF Fusion
        # Rank dict: {doc_id: 1/(rank + 60)}
        rrf_score = {}
        
        # Vector ranks (0-indexed)
        if vector_results['ids']:
            for rank, doc_id in enumerate(vector_results['ids'][0]):
                rrf_score[doc_id] = rrf_score.get(doc_id, 0) + 1.0 / (rank + 60)
            
        # BM25 ranks
        for rank, doc_id in enumerate(bm25_ids):
             rrf_score[doc_id] = rrf_score.get(doc_id, 0) + 1.0 / (rank + 60)
             
        # Sort by RRF score descending
        sorted_ids = sorted(rrf_score.items(), key=lambda item: item[1], reverse=True)
        final_ids = [item[0] for item in sorted_ids[:top_k]]
        
        # Fetch details for final IDs
        if not final_ids:
            return []
            
        final_results = self.collection.get(ids=final_ids)
        
        # Re-construct list of results AND inject Graph Hints
        results = []
        relevant_tables = set()
        
        for i in range(len(final_results['ids'])):
            item = {
                'id': final_results['ids'][i],
                'text': final_results['documents'][i],
                'metadata': final_results['metadatas'][i]
            }
            results.append(item)
            relevant_tables.add(item['metadata']['table'])
            
        # Refinement 4: Inject Join Hints for relevant tables
        for table in relevant_tables:
            if table in self.graph_hints:
                for hint in self.graph_hints[table]:
                    results.append({
                        'id': f"hint_{table}", 
                        'text': f"[GRAPH HINT] {hint}", 
                        'metadata': {'type': 'hint', 'table': table}
                    })
            
        return results


