import json
import logging
from enum import Enum
from typing import Optional, Sequence

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, Prompt, Resource, TextContent, Tool
from pydantic import BaseModel, ConfigDict, Field

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

APP_NAME = "mcp-server-zenn"
APP_VERSION = "0.0.0"

BASE_URL = "https://zenn.dev/api/"
server = Server(APP_NAME)
options = server.create_initialization_options()


class ZennTool(Enum):
    ARTICLE = "article"
    BOOK = "book"

    @staticmethod
    def from_str(tool: str) -> "ZennTool":
        for tool_type in ZennTool:
            if tool_type.value == tool.lower():
                return tool_type
        raise ValueError(f"Invalid tool value: {tool}")


class URLResource(Enum):
    ARTICLES = "articles"
    BOOKS = "books"

    @staticmethod
    def from_str(resource: str) -> "URLResource":
        for resource_type in URLResource:
            if resource_type.value == resource.lower():
                return resource_type
        raise ValueError(f"Invalid resource value: {resource}")

    @staticmethod
    def from_zenn_tool(tool: ZennTool) -> "URLResource":
        if tool == ZennTool.ARTICLE:
            return URLResource.ARTICLES
        elif tool == ZennTool.BOOK:
            return URLResource.BOOKS
        else:
            raise ValueError(f"Invalid tool value: {tool}")

    def to_zenn_tool(self) -> ZennTool:
        if self == URLResource.ARTICLES:
            return ZennTool.ARTICLE
        elif self == URLResource.BOOKS:
            return ZennTool.BOOK
        else:
            raise ValueError(f"Invalid resource value: {self}")


class Order(Enum):
    LATEST = "latest"
    OLDEST = "oldest"

    @staticmethod
    def from_str(order: str) -> "Order":
        for order_type in Order:
            if order_type.value == order.lower():
                return order_type
        raise ValueError(f"Invalid order value: {order}")


class Article(BaseModel):
    """Fetch articles from Zenn.dev"""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=True,
        extra="forbid",
    )

    username: Optional[str] = Field(default=None, description="Username of the article author")
    topicname: Optional[str] = Field(default=None, description="Topic name of the article")
    order: Optional[Order] = Field(
        default=Order.LATEST,
        description=f"Order of the articles. Choose from {Order.LATEST.value} or {Order.OLDEST.value}",
    )
    page: Optional[int] = Field(default=1, description="Page number of the articles. Default: 1")
    count: Optional[int] = Field(default=48, description="Number of articles per page. Default: 48")

    @staticmethod
    def from_arguments(arguments: dict) -> "Article":
        return Article(
            username=arguments.get("username"),
            topicname=arguments.get("topicname"),
            order=Order.from_str(arguments.get("order", Order.LATEST.value)),
            page=arguments.get("page", 1),
            count=arguments.get("count", 48),
        )

    def to_query_param(self) -> dict:
        param = {}
        if self.username:
            param["username"] = self.username.lower()
        if self.topicname:
            param["topicname"] = self.topicname.lower()
        if self.order:
            param["order"] = self.order.value
        if self.page:
            param["page"] = self.page
        if self.count:
            param["count"] = self.count
        return param

    @staticmethod
    def tool() -> Tool:
        return Tool(
            name=ZennTool.ARTICLE.value,
            description="Fetch articles from Zenn.dev",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": Article.model_fields["username"].description},
                    "topicname": {"type": "string", "description": Article.model_fields["topicname"].description},
                    "order": {
                        "type": "string",
                        "description": Article.model_fields["order"].description,
                        "enum": [Order.LATEST.value, Order.OLDEST.value],
                    },
                    "page": {"type": "integer", "description": Article.model_fields["page"].description},
                    "count": {"type": "integer", "description": Article.model_fields["count"].description},
                },
                "required": [],
            },
        )


class Book(BaseModel):
    """Fetch books from Zenn.dev"""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=True,
        extra="forbid",
    )

    username: Optional[str] = Field(default=None, description="Username of the book author")
    topicname: Optional[str] = Field(default=None, description="Topic name of the book")
    order: Optional[Order] = Field(
        default=Order.LATEST,
        description=f"Order of the books. Choose from {Order.LATEST.value} or {Order.OLDEST.value}. Default: {Order.LATEST.value}",
    )
    page: Optional[int] = Field(default=1, description="Page number of the books. Default: 1")
    count: Optional[int] = Field(default=48, description="Number of books per page. Default: 48")

    @staticmethod
    def from_arguments(arguments: dict) -> "Book":
        return Book(
            username=arguments.get("username"),
            topicname=arguments.get("topicname"),
            order=Order.from_str(arguments.get("order", Order.LATEST.value)),
            page=arguments.get("page", 1),
            count=arguments.get("count", 48),
        )

    def to_query_param(self) -> dict:
        param = {}
        if self.username:
            param["username"] = self.username.lower()
        if self.topicname:
            param["topicname"] = self.topicname.lower()
        if self.order:
            param["order"] = self.order.value
        if self.page:
            param["page"] = self.page
        if self.count:
            param["count"] = self.count
        return param

    @staticmethod
    def tool() -> Tool:
        return Tool(
            name=ZennTool.BOOK.value,
            description="Fetch books from Zenn.dev",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": Book.model_fields["username"].description},
                    "topicname": {"type": "string", "description": Book.model_fields["topicname"].description},
                    "order": {
                        "type": "string",
                        "description": Book.model_fields["order"].description,
                        "enum": [Order.LATEST.value, Order.OLDEST.value],
                    },
                    "page": {"type": "integer", "description": Book.model_fields["page"].description},
                    "count": {"type": "integer", "description": Book.model_fields["count"].description},
                },
                "required": [],
            },
        )


async def request(resource: URLResource, query: dict) -> dict:
    url = f"{BASE_URL}{resource.value}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=query)
        response.raise_for_status()
        return response.json()


async def fetch_articles(query: Article) -> dict:
    return await request(URLResource.ARTICLES, query.to_query_param())


async def fetch_books(query: Book) -> dict:
    return await request(URLResource.BOOKS, query.to_query_param())


async def handle_articles(arguments: dict) -> dict:
    query = Article.from_arguments(arguments)
    return await fetch_articles(query)


async def handle_books(arguments: dict) -> dict:
    query = Book.from_arguments(arguments)
    return await fetch_books(query)


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    return []


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return []


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Article.tool(), Book.tool()]


@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    try:
        logger.debug(f"Calling tool: {name} with arguments: {arguments}")
        match name:
            case ZennTool.ARTICLE.value:
                result = await handle_articles(arguments)
            case ZennTool.BOOK.value:
                result = await handle_books(arguments)
            case _:
                raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        logger.error(f"Error processing {APP_NAME} query: {str(e)}")
        raise ValueError(f"Error processing {APP_NAME} query: {str(e)}")


async def serve():
    logger.info("Starting MCP server for Zenn")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=APP_NAME,
                server_version=APP_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
