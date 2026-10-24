from sqlalchemy import text, inspect
from typing import Dict, Any, List, Optional
from app.database import engine
from app.tools.base import BaseTool
from app.utils.logger import logger

class DatabaseTool(BaseTool):
    """
    Tool to run SQL queries and inspect database schemas directly.
    Supports SELECT queries, schema introspection, and table summaries.
    """
    name = "database_query"
    description = (
        "Execute SQL queries on the relational database (SQLite) or inspect database schemas. "
        "Allows querying conversation history, messages, system tables, and custom schemas. "
        "Returns formatted rows and columns."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL query to execute (e.g. 'SELECT * FROM conversations LIMIT 5;' or 'SHOW_TABLES')"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of rows to return (default 20)",
                "default": 20
            }
        },
        "required": ["query"]
    }

    def run(self, query: str, limit: int = 20, **kwargs) -> Dict[str, Any]:
        query_strip = query.strip()
        query_upper = query_strip.upper()

        # Helper command: show tables
        if query_upper in ["SHOW_TABLES", "SHOW TABLES", "LIST TABLES"]:
            return self.inspect_schema()

        try:
            logger.info(f"DatabaseTool executing SQL: {query_strip[:100]}")
            with engine.connect() as conn:
                # Disallow multiple semicolon separated statements for basic safety
                statements = [s for s in query_strip.split(";") if s.strip()]
                if len(statements) > 1:
                    query_to_run = statements[0]
                else:
                    query_to_run = query_strip

                result = conn.execute(text(query_to_run))
                
                # Check if query returns rows (like SELECT or PRAGMA)
                if result.returns_rows:
                    columns = list(result.keys())
                    raw_rows = result.fetchmany(limit)
                    rows = [dict(zip(columns, [str(v) if v is not None else "NULL" for v in row])) for row in raw_rows]
                    
                    # Generate markdown table for rich LLM context
                    md_table = self._format_as_markdown_table(columns, rows)
                    
                    return {
                        "status": "success",
                        "type": "query_result",
                        "row_count": len(rows),
                        "columns": columns,
                        "rows": rows,
                        "markdown_table": md_table
                    }
                else:
                    conn.commit()
                    return {
                        "status": "success",
                        "type": "execution_result",
                        "rows_affected": result.rowcount,
                        "message": "Query executed successfully."
                    }

        except Exception as e:
            logger.error(f"DatabaseTool SQL error: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "message": str(e)
            }

    def inspect_schema(self) -> Dict[str, Any]:
        """Inspects all tables and columns in the active database engine"""
        try:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            schema_info = {}

            for table in table_names:
                cols = inspector.get_columns(table)
                schema_info[table] = [
                    {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
                    for c in cols
                ]

            return {
                "status": "success",
                "type": "schema_inspection",
                "tables_count": len(table_names),
                "tables": table_names,
                "schemas": schema_info
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to inspect schema: {str(e)}"}

    def _format_as_markdown_table(self, columns: List[str], rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "No rows returned."

        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        data_rows = []

        for r in rows:
            row_str = "| " + " | ".join([str(r.get(c, ""))[:40] for c in columns]) + " |"
            data_rows.append(row_str)

        return "\n".join([header, separator] + data_rows)
