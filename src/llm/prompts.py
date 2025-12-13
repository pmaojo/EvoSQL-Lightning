SYSTEM_PROMPT = """You are an expert SQL data analyst."""

AMBIGUITY_PROMPT = """
Given the user query: "{query}"
And the following schema columns: {columns}
Identify if there is any ambiguity. If yes, ask a clarifying question.
"""

GENERATE_SQL_PROMPT = """
Schema:
{schema_context}

Question: {query}
SQL:
"""
