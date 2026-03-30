"""CLI for haraj.com.sa SDK."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from haraj.client import CATEGORIES, HarajClient

console = Console()


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _make_client(ctx: click.Context) -> HarajClient:
    return HarajClient(
        username=ctx.obj.get("username"),
        password=ctx.obj.get("password"),
    )


@click.group()
@click.option("--username", "-u", envvar="HARAJ_USERNAME", help="Haraj username")
@click.option("--password", "-p", envvar="HARAJ_PASSWORD", help="Haraj password")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx: click.Context, username: str | None, password: str | None, json_output: bool) -> None:
    """haraj-sdk: CLI for haraj.com.sa (حراج) marketplace."""
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["json"] = json_output


@cli.command()
@click.option("--tag", "-t", help="Category tag (e.g. 'cars', 'electronics', or Arabic tag)")
@click.option("--city", "-c", help="City filter")
@click.option("--page", default=1, help="Page number")
@click.option("--limit", default=20, help="Results per page")
@click.option("--author", "-a", help="Filter by author username")
@click.option("--images-only", is_flag=True, help="Only posts with images")
@click.pass_context
def posts(ctx: click.Context, tag: str | None, city: str | None, page: int, limit: int, author: str | None, images_only: bool) -> None:
    """Browse posts/listings."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            result = await client.get_posts(
                tag=tag, city=city, page=page, limit=limit,
                author_username=author,
                only_with_image=True if images_only else None,
            )
            if ctx.obj["json"]:
                click.echo(json.dumps([p.model_dump(by_alias=True) for p in result.items], ensure_ascii=False, indent=2))
                return
            _print_posts_table(result.items, result.page_info)

    _run(_run_it())


@cli.command()
@click.argument("keyword")
@click.option("--tag", "-t", help="Category filter")
@click.option("--city", "-c", help="City filter")
@click.option("--page", default=1, help="Page number")
@click.option("--during", help="Time filter: 24hours, 3days, 1week, 1month")
@click.option("--images-only", is_flag=True, help="Only posts with images")
@click.pass_context
def search(ctx: click.Context, keyword: str, tag: str | None, city: str | None, page: int, during: str | None, images_only: bool) -> None:
    """Search listings by keyword."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            result = await client.search(
                keyword=keyword, tag=tag, city=city, page=page,
                during_date=during,
                only_with_image=True if images_only else None,
            )
            if ctx.obj["json"]:
                click.echo(json.dumps([p.model_dump(by_alias=True) for p in result.items], ensure_ascii=False, indent=2))
                return
            _print_posts_table(result.items, result.page_info)

    _run(_run_it())


@cli.command()
@click.argument("post_id", type=int)
@click.pass_context
def post(ctx: click.Context, post_id: int) -> None:
    """Get a single post by ID."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            p = await client.get_post(post_id)
            if not p:
                console.print("[red]Post not found[/red]")
                sys.exit(1)
            if ctx.obj["json"]:
                click.echo(json.dumps(p.model_dump(by_alias=True), ensure_ascii=False, indent=2))
                return
            console.print(f"\n[bold]{p.title}[/bold]")
            console.print(f"By: {p.author_username} | City: {p.city} ({p.geo_city}, {p.geo_neighborhood})")
            console.print(f"Tags: {', '.join(p.tags)}")
            console.print(f"Comments: {p.comment_count} | Likes: {p.up_rank}")
            if p.images_list:
                console.print(f"Images: {len(p.images_list)}")
            console.print(f"\n{p.body}\n")
            console.print(f"URL: {p.full_url}")

    _run(_run_it())


@cli.command()
@click.argument("post_id", type=int)
@click.option("--page", default=1, help="Page number")
@click.pass_context
def comments(ctx: click.Context, post_id: int, page: int) -> None:
    """Get comments for a post."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            items, page_info = await client.get_comments(post_id, page=page)
            if ctx.obj["json"]:
                click.echo(json.dumps([c.model_dump(by_alias=True) for c in items], ensure_ascii=False, indent=2))
                return
            if not items:
                console.print("[dim]No comments[/dim]")
                return
            for c in items:
                prefix = "  ↳ " if c.is_reply else ""
                console.print(f"{prefix}[bold]{c.author_username}[/bold]: {c.body}")
            if page_info.has_next_page:
                console.print(f"\n[dim]More comments available (page {page + 1})[/dim]")

    _run(_run_it())


@cli.command()
@click.argument("post_id", type=int)
@click.argument("message")
@click.option("--reply-to", type=int, help="Reply to a specific comment ID")
@click.pass_context
def comment(ctx: click.Context, post_id: int, message: str, reply_to: int | None) -> None:
    """Post a comment on a listing (message a merchant)."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            await client.login()
            result = await client.submit_comment(post_id, message, reply_to=reply_to)
            if result.get("status"):
                console.print(f"[green]Comment posted successfully (ID: {result.get('commentId')})[/green]")
            else:
                console.print(f"[red]Failed: {result.get('notValidReason', 'Unknown error')}[/red]")

    _run(_run_it())


@cli.command()
@click.argument("post_id", type=int)
@click.pass_context
def contact(ctx: click.Context, post_id: int) -> None:
    """Get contact info for a post's seller."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            if client._username and client._password:
                await client.login()
            info = await client.get_post_contact(post_id)
            if ctx.obj["json"]:
                click.echo(json.dumps(info.model_dump(by_alias=True), ensure_ascii=False, indent=2))
                return
            console.print(f"Contact: {info.contact_text or 'N/A'}")
            if info.contact_mobile:
                console.print(f"Mobile: {info.contact_mobile}")
            if info.should_enable_whatsapp:
                console.print("[green]WhatsApp available[/green]")

    _run(_run_it())


@cli.command()
@click.argument("username")
@click.pass_context
def user(ctx: click.Context, username: str) -> None:
    """Get user profile info."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            u = await client.get_user(username=username)
            if ctx.obj["json"]:
                click.echo(json.dumps(u.model_dump(by_alias=True), ensure_ascii=False, indent=2))
                return
            console.print(f"\n[bold]{u.username}[/bold]")
            console.print(f"ID: {u.id} | Followers: {u.count_followers}")
            console.print(f"Registered: {u.registration_date}")
            if u.rating_summary:
                console.print(f"Rating: +{u.rating_summary.up_rank} / -{u.rating_summary.down_rank}")
            if u.badges:
                console.print(f"Badges: {', '.join(b.badge for b in u.badges)}")

    _run(_run_it())


@cli.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Test login and show account info."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            tokens = await client.login()
            console.print(f"[green]Logged in as: {tokens.username}[/green]")
            console.print(f"Status: {tokens.status}")
            if tokens.count_messages is not None:
                console.print(f"Messages: {tokens.count_messages}")

    _run(_run_it())


@cli.command()
@click.pass_context
def me(ctx: click.Context) -> None:
    """Show authenticated user's profile."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            await client.login()
            profile = await client.get_my_profile()
            if ctx.obj["json"]:
                click.echo(json.dumps(profile.model_dump(by_alias=True), ensure_ascii=False, indent=2))
                return
            console.print(f"\n[bold]{profile.username}[/bold]")
            console.print(f"ID: {profile.id}")
            console.print(f"Followers: {profile.count_followers}")
            console.print(f"Member: {profile.is_member}")

    _run(_run_it())


@cli.command()
@click.pass_context
def categories(ctx: click.Context) -> None:
    """List available categories."""
    table = Table(title="Categories")
    table.add_column("Key", style="cyan")
    table.add_column("Arabic Name", style="green")
    for key, arabic in CATEGORIES.items():
        table.add_row(key, arabic)
    console.print(table)


@cli.command()
@click.pass_context
def provinces(ctx: click.Context) -> None:
    """List provinces/regions."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            provs = await client.get_provinces()
            if ctx.obj["json"]:
                click.echo(json.dumps([p.model_dump(by_alias=True) for p in provs], ensure_ascii=False, indent=2))
                return
            table = Table(title="Provinces")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("English", style="blue")
            for p in provs:
                table.add_row(str(p.id), p.name, p.en_name)
            console.print(table)

    _run(_run_it())


@cli.command()
@click.pass_context
def notifications(ctx: click.Context) -> None:
    """Show user notifications."""

    async def _run_it() -> None:
        async with _make_client(ctx) as client:
            await client.login()
            notes = await client.get_notifications()
            if ctx.obj["json"]:
                click.echo(json.dumps([n.model_dump(by_alias=True) for n in notes], ensure_ascii=False, indent=2))
                return
            if not notes:
                console.print("[dim]No notifications[/dim]")
                return
            for n in notes:
                icon = "[green]●[/green]" if n.is_active else "[dim]○[/dim]"
                console.print(f"{icon} {n.display_title}: {n.display_body}")

    _run(_run_it())


def _print_posts_table(items: list[Any], page_info: Any) -> None:
    from haraj.models import Post

    table = Table(title=f"Listings ({len(items)} results)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="green", max_width=40)
    table.add_column("City", style="blue")
    table.add_column("Author", style="yellow")
    table.add_column("Comments", justify="right")
    table.add_column("Likes", justify="right")
    table.add_column("Images", justify="right")
    for p in items:
        table.add_row(
            str(p.id),
            p.title[:40],
            p.geo_city or p.city,
            p.author_username[:15],
            str(p.comment_count),
            str(p.up_rank),
            str(len(p.images_list)),
        )
    console.print(table)
    if page_info.has_next_page:
        console.print("[dim]More results available (use --page)[/dim]")


if __name__ == "__main__":
    cli()
