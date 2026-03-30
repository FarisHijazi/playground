"""Haraj API client wrapping the GraphQL endpoint at graphql.haraj.com.sa."""

from __future__ import annotations

import uuid
from typing import Any

import httpx

from haraj import queries
from haraj.models import (
    AuthTokens,
    City,
    Comment,
    ContactInfo,
    Notification,
    PageInfo,
    Post,
    PriceInfo,
    Province,
    Rating,
    SearchResult,
    User,
)

GRAPHQL_URL = "https://graphql.haraj.com.sa"
DEFAULT_VERSION = "8.2.9"

# Category constants (Arabic tag names used by haraj.com.sa)
CATEGORIES: dict[str, str] = {
    "cars": "حراج السيارات",
    "real_estate": "حراج العقار",
    "electronics": "حراج الأجهزة",
    "animals": "مواشي وحيوانات وطيور",
    "furniture": "اثاث",
    "jobs": "وظائف",
    "services": "خدمات",
    "fashion": "مستلزمات شخصية",
    "games": "العاب وترفيه",
    "antiques": "نوادر و تراثيات",
    "arts": "مكتبة وفنون",
    "outdoors": "صيد ورحلات",
    "food": "اطعمة ومشروبات",
    "gardens": "زراعة وحدائق",
    "events": "حفلات ومناسبات",
    "travel": "سفر وسياحة",
    "lost_found": "مفقودات",
    "education": "تعليم وتدريب",
    "programming": "برمجة وتصاميم",
    "investments": "مشاريع واستثمارات",
    "other": "قسم غير مصنف",
}


class HarajError(Exception):
    """Raised when the haraj API returns an error."""


class HarajClient:
    """Async client for the haraj.com.sa GraphQL API.

    Supports browsing listings, searching, commenting, messaging,
    authentication, and user profile operations.
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
    ) -> None:
        self._client_id = client_id or str(uuid.uuid4())
        self._http = httpx.AsyncClient(
            headers={"User-Agent": "HarajSDK/0.1.0", "Content-Type": "application/json"},
            timeout=30.0,
        )
        self._access_token: str = access_token or ""
        self._refresh_token: str = refresh_token or ""
        self._username: str = username or ""
        self._password: str = password or ""

    # ── low-level ──

    async def _gql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        query_name: str = "sdk",
    ) -> dict[str, Any]:
        params = {
            "queryName": query_name,
            "token": self._access_token,
            "clientid": self._client_id,
            "version": DEFAULT_VERSION,
        }
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await self._http.post(GRAPHQL_URL, params=params, json=payload)
        if resp.status_code != 200:
            raise HarajError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if "errors" in data:
            raise HarajError(str(data["errors"]))
        return data.get("data", {})

    @property
    def is_authenticated(self) -> bool:
        return bool(self._access_token)

    # ── Auth ──

    async def login(self, username: str | None = None, password: str | None = None) -> AuthTokens:
        """Login with username/password. Returns auth tokens."""
        username = username or self._username
        password = password or self._password
        if not username or not password:
            raise HarajError("Username and password required")
        data = await self._gql(
            queries.LOGIN,
            {"username": username, "password": password, "oldToken": self._refresh_token or "", "loginByURL": None},
            query_name="login",
        )
        tokens = AuthTokens.model_validate(data["login"])
        if not tokens.access_token and tokens.message:
            raise HarajError(f"Login failed: {tokens.message} (status={tokens.status})")
        self._access_token = tokens.access_token
        self._refresh_token = tokens.refresh_token
        self._username = tokens.username or username
        return tokens

    async def refresh_access_token(self) -> AuthTokens:
        """Refresh the access token using the stored refresh token."""
        if not self._refresh_token:
            raise HarajError("No refresh token available")
        data = await self._gql(
            queries.REFRESH_TOKEN,
            {"refreshToken": self._refresh_token},
            query_name="RefreshAccessToken",
        )
        tokens = AuthTokens.model_validate(data["refreshAccessToken"])
        self._access_token = tokens.access_token
        if tokens.refresh_token:
            self._refresh_token = tokens.refresh_token
        return tokens

    async def logout(self, from_all_devices: bool = False) -> None:
        """Logout the current session."""
        await self._gql(
            queries.LOGOUT,
            {"logoutFromOtherDevices": from_all_devices, "token": self._access_token},
            query_name="Logout",
        )
        self._access_token = ""
        self._refresh_token = ""

    # ── Posts (browsing) ──

    async def get_posts(
        self,
        tag: str | None = None,
        city: str | None = None,
        page: int = 1,
        limit: int | None = None,
        author_username: str | None = None,
        only_with_image: bool | None = None,
        post_ids: list[int] | None = None,
    ) -> SearchResult:
        """Browse posts by tag/category, city, author, or IDs."""
        variables: dict[str, Any] = {"page": page}
        if tag:
            variables["tag"] = CATEGORIES.get(tag, tag)
        if city:
            variables["city"] = city
        if limit:
            variables["limit"] = limit
        if author_username:
            variables["authorUsername"] = author_username
        if only_with_image is not None:
            variables["onlyWithImage"] = only_with_image
        if post_ids:
            variables["id"] = post_ids

        data = await self._gql(queries.FETCH_POSTS, variables, query_name=f"detailsPosts_tag_page{page}")
        return SearchResult.model_validate(data["posts"])

    async def get_post(self, post_id: int) -> Post | None:
        """Get a single post by ID."""
        result = await self.get_posts(post_ids=[post_id])
        return result.items[0] if result.items else None

    async def search(
        self,
        keyword: str,
        tag: str | None = None,
        city: str | None = None,
        page: int = 1,
        limit: int | None = None,
        only_with_image: bool | None = None,
        during_date: str | None = None,
    ) -> SearchResult:
        """Search posts by keyword with optional filters.

        during_date: '24hours', '3days', '1week', '1month'
        """
        variables: dict[str, Any] = {"search": keyword, "page": page}
        if tag:
            variables["tag"] = CATEGORIES.get(tag, tag)
        if city:
            variables["city"] = city
        if limit:
            variables["limit"] = limit
        if only_with_image is not None:
            variables["onlyWithImage"] = only_with_image
        if during_date:
            variables["duringDate"] = during_date

        data = await self._gql(queries.SEARCH_POSTS, variables, query_name=f"search_page{page}")
        return SearchResult.model_validate(data["search"])

    async def get_post_prices(self, post_ids: list[int]) -> list[PriceInfo]:
        """Get prices for multiple posts."""
        data = await self._gql(queries.POST_PRICES, {"id": post_ids}, query_name="PostPrices")
        return [PriceInfo.model_validate(p) for p in data.get("postsPrice", [])]

    async def get_post_contact(self, post_id: int) -> ContactInfo:
        """Get contact info for a post (requires auth for full data)."""
        data = await self._gql(
            queries.POST_CONTACT,
            {"postId": post_id, "isManualRequest": True},
            query_name="PostContact",
        )
        return ContactInfo.model_validate(data["postContact"])

    async def get_similar_posts(self, post_id: int) -> list[Post]:
        """Get posts similar to the given post."""
        data = await self._gql(queries.SIMILAR_POSTS, {"id": post_id}, query_name="SimilarPosts")
        result: list[Post] = []
        for group in data.get("similarPosts", {}).get("groupTags", []):
            for item in group.get("posts", {}).get("items", []):
                result.append(Post.model_validate(item))
        return result

    async def get_favorites(self, page: int = 1, limit: int = 20) -> SearchResult:
        """Get the authenticated user's favorite posts."""
        self._require_auth()
        data = await self._gql(
            queries.FAV_POSTS,
            {"token": self._access_token, "page": page, "limit": limit},
            query_name="FavPosts",
        )
        return SearchResult.model_validate(data["favPosts"])

    # ── Comments ──

    async def get_comments(
        self,
        post_id: int,
        page: int = 1,
        newest_first: bool = True,
    ) -> tuple[list[Comment], PageInfo]:
        """Get comments for a post."""
        data = await self._gql(
            queries.GET_COMMENTS,
            {
                "postId": post_id,
                "page": page,
                "token": self._access_token or None,
                "newestFirst": newest_first,
            },
            query_name=f"Comments_page{page}",
        )
        comments_data = data.get("comments", {})
        items = [Comment.model_validate(c) for c in comments_data.get("items", [])]
        page_info = PageInfo.model_validate(comments_data.get("pageInfo", {}))
        return items, page_info

    async def submit_comment(
        self, post_id: int, comment: str, reply_to: int | None = None
    ) -> dict[str, Any]:
        """Post a comment on a listing. This is the primary way to message merchants."""
        self._require_auth()
        variables: dict[str, Any] = {
            "token": self._access_token,
            "postId": post_id,
            "comment": comment,
        }
        if reply_to:
            variables["replyToCommentId"] = reply_to
        data = await self._gql(queries.SUBMIT_COMMENT, variables, query_name="SubmitComment")
        return data.get("submitComment", {})

    async def delete_comment(self, comment_id: int, block_commenter: bool = False) -> dict[str, Any]:
        """Delete a comment."""
        self._require_auth()
        data = await self._gql(
            queries.DELETE_COMMENT,
            {"token": self._access_token, "id": comment_id, "blockCommentator": block_commenter},
            query_name="DeleteComment",
        )
        return data.get("deleteComment", {})

    # ── User ──

    async def get_user(
        self, username: str | None = None, user_id: int | None = None
    ) -> User:
        """Get user profile info."""
        variables: dict[str, Any] = {}
        if username:
            variables["username"] = username
        if user_id:
            variables["id"] = user_id
        if self._access_token:
            variables["token"] = self._access_token
        data = await self._gql(queries.GET_USER, variables, query_name="User")
        return User.model_validate(data["user"])

    async def get_my_profile(self) -> User:
        """Get the authenticated user's profile."""
        self._require_auth()
        return await self.get_user(username=self._username)

    async def get_user_posts(self, username: str, page: int = 1) -> SearchResult:
        """Get posts by a specific user."""
        return await self.get_posts(author_username=username, page=page)

    async def get_user_ratings(self, username: str, page: int = 1) -> tuple[list[Rating], PageInfo]:
        """Get ratings for a user."""
        data = await self._gql(
            queries.USER_RATINGS,
            {"username": username, "page": page},
            query_name="RatingsList",
        )
        ratings_data = data.get("ratings", {})
        items = [Rating.model_validate(r) for r in ratings_data.get("items", [])]
        page_info = PageInfo.model_validate(ratings_data.get("pageInfo", {}))
        return items, page_info

    # ── Social ──

    async def like_post(self, post_id: int) -> None:
        """Like a post."""
        self._require_auth()
        await self._gql(
            queries.SUBMIT_LIKE,
            {"token": self._access_token, "id": post_id},
            query_name="SubmitLike",
        )

    async def unlike_post(self, post_id: int) -> None:
        """Remove like from a post."""
        self._require_auth()
        await self._gql(
            queries.REMOVE_LIKE,
            {"token": self._access_token, "id": post_id},
            query_name="RemoveLike",
        )

    async def follow_user(self, username: str) -> None:
        """Follow a user."""
        self._require_auth()
        await self._gql(
            queries.FOLLOW_USER,
            {"token": self._access_token, "username": username},
            query_name="FollowUser",
        )

    async def unfollow_user(self, username: str) -> None:
        """Unfollow a user."""
        self._require_auth()
        await self._gql(
            queries.UNFOLLOW_USER,
            {"token": self._access_token, "username": username},
            query_name="UnFollowUser",
        )

    async def follow_post(self, post_id: int) -> None:
        """Follow a post for updates."""
        self._require_auth()
        await self._gql(
            queries.FOLLOW_POST,
            {"token": self._access_token, "postId": post_id},
            query_name="FollowPost",
        )

    async def get_following_users(self) -> list[dict[str, Any]]:
        """Get list of users the authenticated user follows."""
        self._require_auth()
        data = await self._gql(
            queries.FOLLOWING_USERS,
            {"token": self._access_token},
            query_name="FollowingUsers",
        )
        return data.get("followingUsers", {}).get("followedUsers", [])

    # ── Notifications ──

    async def get_notifications(self, set_read: bool = False) -> list[Notification]:
        """Get user notifications."""
        self._require_auth()
        data = await self._gql(
            queries.GET_NOTES,
            {"token": self._access_token, "setRead": set_read},
            query_name="GetNotes",
        )
        return [Notification.model_validate(n) for n in data.get("notes", {}).get("items", [])]

    # ── Locations ──

    async def get_provinces(self) -> list[Province]:
        """List all provinces/regions."""
        data = await self._gql(queries.LIST_PROVINCES, query_name="ListProvinces")
        return [Province.model_validate(p) for p in data.get("ListProvinces", [])]

    async def get_cities(self, province_id: int) -> list[City]:
        """List cities in a province."""
        data = await self._gql(queries.LIST_CITIES, {"provinceId": province_id}, query_name="ListCities")
        return [City.model_validate(c) for c in data.get("ListCities", [])]

    # ── Search helpers ──

    async def search_suggest(self, chars: str, tag: str | None = None) -> list[str]:
        """Get search keyword suggestions."""
        variables: dict[str, Any] = {"initialChars": chars}
        if tag:
            variables["tag"] = CATEGORIES.get(tag, tag)
        data = await self._gql(queries.SEARCH_SUGGEST, variables, query_name="SearchSuggest")
        return data.get("searchSuggest", {}).get("keywords", [])

    async def get_related_tags(self, tag: str, city: str | None = None) -> list[dict[str, Any]]:
        """Get related tags for a category."""
        tag_value = CATEGORIES.get(tag, tag)
        data = await self._gql(
            queries.RELATED_TAGS,
            {"tag": tag_value, "city": city},
            query_name="GetRelatedTags",
        )
        return data.get("relatedTags", [])

    # ── Helpers ──

    def _require_auth(self) -> None:
        if not self._access_token:
            raise HarajError("Authentication required. Call login() first.")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> HarajClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
