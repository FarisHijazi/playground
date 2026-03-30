"""Pydantic models for haraj.com.sa API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PageInfo(BaseModel):
    has_next_page: bool = Field(alias="hasNextPage", default=False)
    has_previous_page: bool = Field(alias="hasPreviousPage", default=False)
    total_count: int | None = Field(alias="totalCount", default=None)
    current_page: int | None = Field(alias="currentPage", default=None)

    model_config = {"populate_by_name": True}


class CarInfo(BaseModel):
    sell_or_waiver: str | None = Field(alias="sellOrWaiver", default=None)
    model: int | None = None
    mileage: int | None = None
    fuel: str | None = None
    gear: str | None = None
    condition: str | None = None
    car_or_related: str | None = Field(alias="carOrRelated", default=None)

    model_config = {"populate_by_name": True}


class PriceInfo(BaseModel):
    post_id: int | None = Field(alias="postId", default=None)
    formatted_price: str | None = Field(alias="formattedPrice", default=None)
    input_price: str | None = Field(alias="inputPrice", default=None)

    model_config = {"populate_by_name": True}


class ExtraInfo(BaseModel):
    key: str
    value: str | None = None


class Post(BaseModel):
    id: int
    title: str = ""
    body: str = Field(alias="bodyTEXT", default="")
    body_html: str = Field(alias="bodyHTML", default="")
    author_username: str = Field(alias="authorUsername", default="")
    author_id: int | None = Field(alias="authorId", default=None)
    city: str = ""
    geo_city: str = Field(alias="geoCity", default="")
    geo_neighborhood: str = Field(alias="geoNeighborhood", default="")
    geo_hash: str = Field(alias="geoHash", default="")
    post_date: int | None = Field(alias="postDate", default=None)
    update_date: int | None = Field(alias="updateDate", default=None)
    has_image: bool = Field(alias="hasImage", default=False)
    has_video: bool = Field(alias="hasVideo", default=False)
    thumb_url: str = Field(alias="thumbURL", default="")
    images_list: list[str] = Field(alias="imagesList", default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tags_filters: list[str] = Field(alias="tagsFilters", default_factory=list)
    comment_count: int = Field(alias="commentCount", default=0)
    comment_enabled: bool = Field(alias="commentEnabled", default=True)
    comment_status: str | int | None = Field(alias="commentStatus", default=None)
    up_rank: int = Field(alias="upRank", default=0)
    down_rank: int = Field(alias="downRank", default=0)
    status: bool | str | None = None
    post_type: str | None = Field(alias="postType", default=None)
    is_promoted: bool = Field(alias="isPromoted", default=False)
    url: str = Field(alias="URL", default="")
    price: PriceInfo | None = None
    car_info: CarInfo | None = Field(alias="carInfo", default=None)
    general_info: list[ExtraInfo] | None = Field(alias="generalInfo", default=None)

    model_config = {"populate_by_name": True}

    @property
    def full_url(self) -> str:
        return self.url or f"https://haraj.com.sa/11{self.id}/"

    @property
    def full_thumb_url(self) -> str:
        if not self.thumb_url:
            return ""
        if self.thumb_url.startswith("http"):
            return self.thumb_url
        return f"https://mimg6cdn.haraj.com.sa/userfiles30/{self.thumb_url}"


class Comment(BaseModel):
    id: int
    body: str = ""
    author_username: str = Field(alias="authorUsername", default="")
    author_id: int | None = Field(alias="authorId", default=None)
    author_level: str | int | None = Field(alias="authorLevel", default=None)
    date: str | int | None = None
    status: str | int | None = None
    is_new_user: bool = Field(alias="isNewUser", default=False)
    is_reply: bool = Field(alias="isReply", default=False)
    reply_to_comment_id: int | None = Field(alias="replyToCommentId", default=None)
    seq_id: int | None = Field(alias="seqId", default=None)
    delete_reason: str | None = Field(alias="deleteReason", default=None)

    model_config = {"populate_by_name": True}


class RatingSummary(BaseModel):
    up_rank: int = Field(alias="upRank", default=0)
    down_rank: int = Field(alias="downRank", default=0)
    up_paid_rank: int = Field(alias="upPaidRank", default=0)
    down_paid_rank: int = Field(alias="downPaidRank", default=0)
    rate_average: float | None = Field(alias="rateAverage", default=None)

    model_config = {"populate_by_name": True}


class Subscription(BaseModel):
    type: str | None = None
    join_date: str | None = Field(alias="joinDate", default=None)
    expiration_date: str | None = Field(alias="expirationDate", default=None)
    must_join_type: str | None = Field(alias="mustJoinType", default=None)
    is_active: bool = Field(alias="isActive", default=False)

    model_config = {"populate_by_name": True}


class Badge(BaseModel):
    badge: str = ""


class User(BaseModel):
    id: int | None = None
    username: str = ""
    handler: str | None = None
    registration_date: str | int | None = Field(alias="registrationDate", default=None)
    count_followers: int | None = Field(alias="countFollowers", default=None)
    mobile: str | None = None
    email: str | None = None
    discount: str | None = None
    is_member: bool | None = Field(alias="isMember", default=None)
    is_admin: bool | None = Field(alias="isAdmin", default=None)
    is_blocked: bool | None = Field(alias="isBlocked", default=None)
    did_pay: bool | None = Field(alias="didPay", default=None)
    last_seen: str | int | None = Field(alias="lastSeen", default=None)
    message_to_user: str | None = Field(alias="messageToUser", default=None)
    subscription: Subscription | None = None
    rating_summary: RatingSummary | None = Field(alias="ratingSummery", default=None)
    badges: list[Badge] | None = Field(default=None)
    is_realtor: bool | None = Field(alias="isRealtor", default=None)
    linked_via_nafath: bool | None = Field(alias="linkedViaNafath", default=None)
    vat_number: str | None = Field(alias="VATNumber", default=None)

    model_config = {"populate_by_name": True}


class Rating(BaseModel):
    id: int
    vote: str | None = None
    rating_text: str = Field(alias="rating_text", default="")
    buyer_name: str = Field(alias="buyer_name", default="")
    is_paid: bool = Field(alias="isPaid", default=False)
    seller_feedback: str | None = Field(alias="sellerFeedback", default=None)
    date: str | None = None

    model_config = {"populate_by_name": True}


class ContactInfo(BaseModel):
    contact_text: str | None = Field(alias="contactText", default=None)
    contact_mobile: str | None = Field(alias="contactMobile", default=None)
    should_enable_whatsapp: bool = Field(alias="shouldEnableWhatsApp", default=False)

    model_config = {"populate_by_name": True}


class SearchResult(BaseModel):
    items: list[Post] = Field(default_factory=list)
    page_info: PageInfo = Field(alias="pageInfo", default_factory=PageInfo)

    model_config = {"populate_by_name": True}


class AuthTokens(BaseModel):
    access_token: str = Field(alias="accessToken", default="")
    refresh_token: str = Field(alias="refreshToken", default="")
    at_valid_until: str | int | None = Field(alias="ATvalidUntil", default=None)
    rt_valid_until: str | int | None = Field(alias="RTvalidUntil", default=None)
    ul: int | None = None
    username: str = ""
    message: str = ""
    status: str | int = ""
    count_messages: int | None = Field(alias="countMessages", default=None)
    count_notes: int | None = Field(alias="countNotes", default=None)

    model_config = {"populate_by_name": True}


class Notification(BaseModel):
    type: str | None = None
    display_title: str = Field(alias="displayTitle", default="")
    display_body: str = Field(alias="displayBody", default="")
    related_user: str | None = Field(alias="related_user", default=None)
    related_ads_num: int | None = Field(alias="related_ads_num", default=None)
    thumb_url: str = Field(alias="thumbURL", default="")
    is_active: bool = Field(alias="isActive", default=False)
    tag: str | None = None
    date: str | None = None
    city: str | None = None
    url: str | None = None
    view_type: str | None = Field(alias="viewType", default=None)

    model_config = {"populate_by_name": True}


class Province(BaseModel):
    id: int
    name: str = ""
    en_name: str = Field(alias="enName", default="")

    model_config = {"populate_by_name": True}


class City(BaseModel):
    id: int
    name: str = ""
    en_name: str = Field(alias="enName", default="")
    lat: float | None = None
    lon: float | None = None

    model_config = {"populate_by_name": True}
