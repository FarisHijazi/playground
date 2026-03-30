# haraj-sdk

Python SDK, CLI, and MCP server for [haraj.com.sa](https://haraj.com.sa) (حراج) — Saudi Arabia's largest classifieds marketplace.

## Install

```bash
pip install haraj-sdk
# or with uv
uv pip install haraj-sdk
```

## Quick Start

### Python SDK

```python
import asyncio
from haraj import HarajClient

async def main():
    async with HarajClient() as client:
        # Browse car listings
        result = await client.get_posts(tag="cars", city="الرياض", page=1)
        for post in result.items:
            print(f"{post.title} - {post.geo_city}")

        # Search listings
        results = await client.search("iphone", tag="electronics")
        for post in results.items:
            print(f"{post.title} ({post.comment_count} comments)")

        # Get a single listing
        post = await client.get_post(177829453)
        print(post.body)

        # Get comments
        comments, page_info = await client.get_comments(177829453)
        for c in comments:
            print(f"{c.author_username}: {c.body}")

        # Get user profile
        user = await client.get_user(username="FarisHijazi")
        print(f"Followers: {user.count_followers}")

asyncio.run(main())
```

### Authenticated Operations

```python
async with HarajClient(username="user", password="pass") as client:
    await client.login()

    # Comment on a listing (message a merchant)
    await client.submit_comment(post_id=12345, comment="Is this still available?")

    # Like a post
    await client.like_post(12345)

    # Get notifications
    notes = await client.get_notifications()

    # Get favorites
    favs = await client.get_favorites()
```

## CLI

```bash
# Browse listings
haraj posts --tag cars --city الرياض
haraj posts --tag electronics --images-only

# Search
haraj search "iphone 16" --tag electronics

# View a single listing
haraj post 177829453

# Get comments
haraj comments 177829453

# Get seller contact
haraj contact 177829453

# User profile
haraj user "FarisHijazi"

# Categories and provinces
haraj categories
haraj provinces

# Login and comment (message merchant)
haraj -u USERNAME -p PASSWORD comment 12345 "Is this available?"

# Login test
haraj -u USERNAME -p PASSWORD login

# JSON output
haraj -j posts --tag cars --limit 5
```

Environment variables `HARAJ_USERNAME` and `HARAJ_PASSWORD` can be used instead of `-u` and `-p`.

## MCP Server

Run the MCP server for use with AI assistants:

```bash
# Run directly
python -m haraj.mcp_server

# Or use with Claude/Cursor config:
{
    "mcpServers": {
        "haraj": {
            "command": "uv",
            "args": ["run", "--directory", "/path/to/haraj-sdk", "python", "-m", "haraj.mcp_server"],
            "env": {
                "HARAJ_USERNAME": "your_username",
                "HARAJ_PASSWORD": "your_password"
            }
        }
    }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `browse_listings` | Browse by category, city, or author |
| `search_listings` | Search by keyword |
| `get_listing` | Get full listing details |
| `get_listing_comments` | Get comments on a listing |
| `post_comment` | Post a comment (message merchant) |
| `get_seller_contact` | Get seller contact info |
| `get_user_profile` | Get user profile |
| `get_user_listings` | Get a user's listings |
| `get_user_ratings` | Get user ratings |
| `like_listing` | Like a listing |
| `get_my_notifications` | Get notifications |
| `list_categories` | List categories |
| `list_provinces` | List provinces |
| `search_suggestions` | Get search suggestions |

## Categories

| Key | Arabic |
|-----|--------|
| `cars` | حراج السيارات |
| `real_estate` | حراج العقار |
| `electronics` | حراج الأجهزة |
| `animals` | مواشي وحيوانات وطيور |
| `furniture` | اثاث |
| `jobs` | وظائف |
| `services` | خدمات |
| `fashion` | مستلزمات شخصية |
| `games` | العاب وترفيه |
| `antiques` | نوادر و تراثيات |
| `arts` | مكتبة وفنون |
| `outdoors` | صيد ورحلات |
| `food` | اطعمة ومشروبات |
| `gardens` | زراعة وحدائق |
| `events` | حفلات ومناسبات |
| `travel` | سفر وسياحة |
| `lost_found` | مفقودات |
| `education` | تعليم وتدريب |
| `programming` | برمجة وتصاميم |
| `investments` | مشاريع واستثمارات |
| `other` | قسم غير مصنف |
