import sys
import io
import contextlib
import traceback
from typing import Dict, Any
from app.tools.base import BaseTool
from app.utils.logger import logger

class CodeExecutorTool(BaseTool):
    """
    Tool to safely execute Python code snippets for calculations, data transformations,
    or algorithm testing.
    """
    name = "code_executor"
    description = (
        "Execute Python code snippets in a safe isolated namespace. "
        "Captures printed output, variable assignments, and return evaluations. "
        "Useful for mathematical calculations, data formatting, and logical computations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to execute"
            }
        },
        "required": ["code"]
    }

    # Safe builtins
    SAFE_BUILTINS = {
        "print": print,
        "range": range,
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "set": set,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "True": True,
        "False": False,
        "None": None
    }

    def run(self, code: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"CodeExecutorTool running code snippet ({len(code)} chars)")
        stdout_capture = io.StringIO()
        
        # Safe globals dictionary
        exec_globals = {
            "__builtins__": self.SAFE_BUILTINS,
            "math": __import__("math"),
            "json": __import__("json"),
            "datetime": __import__("datetime"),
            "re": __import__("re")
        }
        exec_locals = {}

        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(code, exec_globals, exec_locals)

            output = stdout_capture.getvalue()
            
            # If no print output, check if any variables were computed
            if not output and exec_locals:
                output = "\n".join([f"{k} = {v}" for k, v in exec_locals.items() if not k.startswith("_")])

            if not output:
                output = "Code executed successfully with no output."

            return {
                "status": "success",
                "output": output.strip()
            }

        except Exception as e:
            logger.error(f"CodeExecutorTool execution error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
