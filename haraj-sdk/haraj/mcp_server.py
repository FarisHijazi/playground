"""MCP server exposing haraj.com.sa SDK as tools."""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from haraj.client import CATEGORIES, HarajClient

mcp = FastMCP(
    "haraj",
    instructions="Tools for interacting with haraj.com.sa (حراج), Saudi Arabia's largest classifieds marketplace.",
)

_client: HarajClient | None = None


def _get_client() -> HarajClient:
    global _client
    if _client is None:
        _client = HarajClient(
            username=os.environ.get("HARAJ_USERNAME"),
            password=os.environ.get("HARAJ_PASSWORD"),
        )
    return _client


async def _ensure_auth(client: HarajClient) -> None:
    if not client.is_authenticated and client._username and client._password:
        await client.login()


def _posts_to_json(posts: list) -> str:
    return json.dumps(
        [p.model_dump(by_alias=True, exclude_none=True) for p in posts],
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def browse_listings(
    category: str | None = None,
    city: str | None = None,
    page: int = 1,
    limit: int = 20,
    author_username: str | None = None,
    only_with_image: bool = False,
) -> str:
    """Browse haraj.com.sa listings by category, city, or author.

    Categories: cars, real_estate, electronics, animals, furniture, jobs,
    services, fashion, games, antiques, arts, outdoors, food, gardens,
    events, travel, lost_found, education, programming, investments, other.
    Or use the Arabic category name directly.
    """
    client = _get_client()
    result = await client.get_posts(
        tag=category, city=city, page=page, limit=limit,
        author_username=author_username,
        only_with_image=only_with_image or None,
    )
    return _posts_to_json(result.items)


@mcp.tool()
async def search_listings(
    keyword: str,
    category: str | None = None,
    city: str | None = None,
    page: int = 1,
    limit: int = 20,
    during_date: str | None = None,
    only_with_image: bool = False,
) -> str:
    """Search haraj.com.sa listings by keyword.

    during_date options: 24hours, 3days, 1week, 1month
    """
    client = _get_client()
    result = await client.search(
        keyword=keyword, tag=category, city=city, page=page,
        limit=limit, during_date=during_date,
        only_with_image=only_with_image or None,
    )
    return _posts_to_json(result.items)


@mcp.tool()
async def get_listing(post_id: int) -> str:
    """Get full details of a single haraj listing by its ID."""
    client = _get_client()
    post = await client.get_post(post_id)
    if not post:
        return json.dumps({"error": "Post not found"})
    data = post.model_dump(by_alias=True, exclude_none=True)
    prices = await client.get_post_prices([post_id])
    if prices:
        data["price"] = prices[0].model_dump(by_alias=True, exclude_none=True)
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_listing_comments(post_id: int, page: int = 1) -> str:
    """Get comments on a haraj listing."""
    client = _get_client()
    comments, page_info = await client.get_comments(post_id, page=page)
    return json.dumps(
        {
            "comments": [c.model_dump(by_alias=True, exclude_none=True) for c in comments],
            "hasNextPage": page_info.has_next_page,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def post_comment(post_id: int, message: str, reply_to_comment_id: int | None = None) -> str:
    """Post a comment on a listing (message a merchant). Requires HARAJ_USERNAME and HARAJ_PASSWORD env vars."""
    client = _get_client()
    await _ensure_auth(client)
    result = await client.submit_comment(post_id, message, reply_to=reply_to_comment_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_seller_contact(post_id: int) -> str:
    """Get seller contact information for a listing. Login gives more details."""
    client = _get_client()
    await _ensure_auth(client)
    info = await client.get_post_contact(post_id)
    return json.dumps(info.model_dump(by_alias=True, exclude_none=True), ensure_ascii=False, indent=2)


@mcp.tool()
async def get_user_profile(username: str) -> str:
    """Get a haraj user's profile information."""
    client = _get_client()
    user = await client.get_user(username=username)
    return json.dumps(user.model_dump(by_alias=True, exclude_none=True), ensure_ascii=False, indent=2)


@mcp.tool()
async def get_user_listings(username: str, page: int = 1) -> str:
    """Get all listings posted by a specific user."""
    client = _get_client()
    result = await client.get_user_posts(username, page=page)
    return _posts_to_json(result.items)


@mcp.tool()
async def get_user_ratings(username: str, page: int = 1) -> str:
    """Get ratings/reviews for a haraj user."""
    client = _get_client()
    ratings, page_info = await client.get_user_ratings(username, page=page)
    return json.dumps(
        {
            "ratings": [r.model_dump(by_alias=True, exclude_none=True) for r in ratings],
            "hasNextPage": page_info.has_next_page,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def like_listing(post_id: int) -> str:
    """Like a haraj listing. Requires authentication."""
    client = _get_client()
    await _ensure_auth(client)
    await client.like_post(post_id)
    return json.dumps({"status": "liked", "postId": post_id})


@mcp.tool()
async def get_my_notifications() -> str:
    """Get the authenticated user's notifications. Requires authentication."""
    client = _get_client()
    await _ensure_auth(client)
    notes = await client.get_notifications()
    return json.dumps(
        [n.model_dump(by_alias=True, exclude_none=True) for n in notes],
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def list_categories() -> str:
    """List all available haraj.com.sa categories with their Arabic names."""
    return json.dumps(CATEGORIES, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_provinces() -> str:
    """List all Saudi provinces/regions available on haraj."""
    client = _get_client()
    provs = await client.get_provinces()
    return json.dumps(
        [p.model_dump(by_alias=True, exclude_none=True) for p in provs],
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def search_suggestions(chars: str, category: str | None = None) -> str:
    """Get search keyword suggestions as the user types."""
    client = _get_client()
    suggestions = await client.search_suggest(chars, tag=category)
    return json.dumps(suggestions, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
