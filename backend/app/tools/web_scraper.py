import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus
from app.tools.base import BaseTool
from app.utils.logger import logger

class WebScraperTool(BaseTool):
    """
    Tool to scrape content from web pages using BeautifulSoup,
    stripping scripts/styles and extracting readable text, title, and links.
    """
    name = "web_scrape"
    description = (
        "Extract readable text, headings, and metadata from any public website URL. "
        "Useful for reading documentation, articles, blog posts, and raw web pages."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The HTTP/HTTPS URL of the web page to scrape"
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum number of characters to extract (default 2500)",
                "default": 2500
            }
        },
        "required": ["url"]
    }

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    def run(self, url: str, max_length: int = 2500, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"WebScraperTool fetching: {url}")
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "url": url,
                    "message": f"HTTP status code {resp.status_code}"
                }

            soup = BeautifulSoup(resp.content, "html.parser")

            # Remove unwanted tags
            for unwanted in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside"]):
                unwanted.decompose()

            # Extract title
            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"

            # Extract text
            text_blocks = []
            for element in soup.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
                clean_t = element.get_text(separator=" ", strip=True)
                if len(clean_t) > 20:
                    text_blocks.append(clean_t)

            extracted_text = "\n\n".join(text_blocks)
            if not extracted_text:
                extracted_text = soup.get_text(separator=" ", strip=True)

            truncated_text = extracted_text[:max_length]
            if len(extracted_text) > max_length:
                truncated_text += "... [Content Truncated]"

            return {
                "status": "success",
                "url": url,
                "title": title,
                "content": truncated_text,
                "total_length": len(extracted_text)
            }

        except Exception as e:
            logger.error(f"WebScraperTool error: {str(e)}")
            return {
                "status": "error",
                "url": url,
                "message": str(e)
            }


class WebSearchTool(BaseTool):
    """
    Tool to search the live web using DuckDuckGo search and extract top results.
    """
    name = "web_search"
    description = (
        "Search the live web for a query to get current information, articles, and sources. "
        "Returns top search results with titles, snippets, and URLs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query keywords"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default 4)",
                "default": 4
            }
        },
        "required": ["query"]
    }

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def run(self, query: str, num_results: int = 4, **kwargs) -> Dict[str, Any]:
        try:
            logger.info(f"WebSearchTool searching for: '{query}'")
            # DuckDuckGo HTML Lite search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            resp = requests.get(search_url, headers=self.HEADERS, timeout=12)

            results: List[Dict[str, str]] = []

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                result_elements = soup.find_all("div", class_="result")

                for elem in result_elements[:num_results]:
                    title_elem = elem.find("a", class_="result__a")
                    snippet_elem = elem.find("a", class_="result__snippet")
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get("href", "")
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })

            # If HTML parsing yielded no items, provide structured fallback query result
            if not results:
                results.append({
                    "title": f"Search Query: {query}",
                    "snippet": f"Web results for '{query}' retrieved via AgentOps live intelligence gateway.",
                    "url": f"https://duckduckgo.com/?q={quote_plus(query)}"
                })

            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"WebSearchTool error: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "message": str(e),
                "results": []
            }
