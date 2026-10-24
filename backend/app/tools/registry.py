import time
import json
import uuid
from typing import Dict, Any, List, Optional
from app.tools.base import BaseTool
from app.tools.api_caller import APICallerTool
from app.tools.web_scraper import WebScraperTool, WebSearchTool
from app.tools.database_tool import DatabaseTool
from app.tools.code_executor import CodeExecutorTool
from app.database import SessionLocal
from app.models import ToolExecutionLog
from app.utils.logger import logger

class ToolRegistry:
    """
    Central Tool Registry managing tool registration, prompt documentation generation,
    dispatching execution, and telemetry logging.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with schemas"""
        return [tool.to_dict() for tool in self._tools.values()]

    def get_tools_description_for_prompt(self) -> str:
        """Generates formatted string describing all available tools for prompt injection"""
        return "\n\n".join([tool.format_description_for_prompt() for tool in self._tools.values()])

    def get_tool_names(self) -> str:
        """Returns comma-separated list of tool names"""
        return ", ".join(self._tools.keys())

    def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Executes a registered tool by name, measures duration, and logs telemetry to DB.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "status": "error",
                "message": f"Tool '{tool_name}' not found. Available tools: {self.get_tool_names()}"
            }

        start_time = time.time()
        status = "success"
        result: Any = None

        try:
            # Flatten params if nested under query or args
            if isinstance(params, dict):
                result = tool.run(**params)
            else:
                result = tool.run(query=str(params))
        except Exception as e:
            status = "error"
            result = {"status": "error", "message": str(e)}
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")

        duration_ms = (time.time() - start_time) * 1000.0

        # Log execution to database
        self._log_tool_execution(tool_name, params, result, status, duration_ms)

        return result

    def _log_tool_execution(self, tool_name: str, params: Any, result: Any, status: str, duration_ms: float) -> None:
        try:
            with SessionLocal() as db:
                log_entry = ToolExecutionLog(
                    id=str(uuid.uuid4()),
                    tool_name=tool_name,
                    input_params=json.dumps(params, default=str)[:1000],
                    output_result=json.dumps(result, default=str)[:1500],
                    status=status,
                    duration_ms=round(duration_ms, 2)
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to write tool execution log to DB: {str(e)}")

    def _register_default_tools(self) -> None:
        self.register(APICallerTool())
        self.register(WebScraperTool())
        self.register(WebSearchTool())
        self.register(DatabaseTool())
        self.register(CodeExecutorTool())

# Global registry instance
global_tool_registry = ToolRegistry()
