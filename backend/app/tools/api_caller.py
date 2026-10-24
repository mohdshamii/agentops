import requests
from typing import Dict, Any, Optional
from app.tools.base import BaseTool
from app.utils.logger import logger

class APICallerTool(BaseTool):
    """
    Tool that allows the agent to make arbitrary HTTP requests (GET, POST, PUT, DELETE)
    to REST APIs or built-in presets.
    """
    name = "api_caller"
    description = (
        "Execute REST API calls with support for GET, POST, PUT, DELETE, query params, headers, and JSON body. "
        "Useful for fetching live data from third-party services or testing APIs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Full HTTP/HTTPS URL of the endpoint"
            },
            "method": {
                "type": "string",
                "description": "HTTP Method: GET, POST, PUT, DELETE. Defaults to GET.",
                "default": "GET"
            },
            "headers": {
                "type": "object",
                "description": "Optional HTTP headers dictionary",
                "default": {}
            },
            "params": {
                "type": "object",
                "description": "Optional URL query parameters dictionary",
                "default": {}
            },
            "data": {
                "type": "object",
                "description": "Optional JSON payload for POST/PUT requests",
                "default": {}
            }
        },
        "required": ["url"]
    }

    # Public presets for fast query resolution
    PRESETS = {
        "crypto_prices": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd",
        "mock_users": "https://jsonplaceholder.typicode.com/users",
        "mock_posts": "https://jsonplaceholder.typicode.com/posts?_limit=5",
        "ip_info": "https://ipapi.co/json/"
    }

    def run(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        method = method.upper()
        headers = headers or {"User-Agent": "AgentOps-AI-Client/2.0"}

        # Resolve preset shortcuts if provided
        if url in self.PRESETS:
            url = self.PRESETS[url]

        try:
            logger.info(f"APICallerTool executing {method} on {url}")
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=15)
            elif method == "POST":
                resp = requests.post(url, headers=headers, params=params, json=data, timeout=15)
            elif method == "PUT":
                resp = requests.put(url, headers=headers, params=params, json=data, timeout=15)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, params=params, timeout=15)
            else:
                return {"status": "error", "message": f"Unsupported HTTP method: {method}"}

            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                body = resp.json()
            else:
                body = resp.text[:2000]

            return {
                "status": "success",
                "status_code": resp.status_code,
                "url": url,
                "data": body
            }

        except Exception as e:
            logger.error(f"APICallerTool error: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "message": str(e)
            }
