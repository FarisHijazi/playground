"""GraphQL queries and mutations for haraj.com.sa API."""

# ── Post fields fragment ──
POST_FIELDS = """
    id status authorUsername title city postDate updateDate
    hasImage hasVideo thumbURL authorId bodyHTML bodyTEXT
    tags tagsFilters imagesList commentEnabled commentStatus commentCount
    upRank downRank geoHash geoCity geoNeighborhood
    isPromoted postType URL
    generalInfo { key value }
"""

# ── Auth ──
LOGIN = """
mutation login($username: String!, $password: String!, $oldToken: String!, $loginByURL: String) {
  login(username: $username, password: $password, oldRefreshToken: $oldToken, loginByURL: $loginByURL) {
    accessToken ATvalidUntil refreshToken RTvalidUntil ul username message status
  }
}
"""

REFRESH_TOKEN = """
mutation RefreshAccessToken($refreshToken: String!) {
  refreshAccessToken(refreshToken: $refreshToken) {
    accessToken refreshToken ATvalidUntil ul status username countMessages countNotes message
  }
}
"""

LOGOUT = """
mutation Logout($logoutFromOtherDevices: Boolean!, $token: String!) {
  logout(logoutFromOtherDevices: $logoutFromOtherDevices, token: $token)
}
"""

# ── Posts ──
FETCH_POSTS = f"""
query FetchAds(
  $id: [Int] = null, $city: String = null, $cities: [String],
  $authorUsername: String = null, $page: Int = null, $limit: Int = null,
  $afterPostDate: Int = null, $afterUpdateDate: Int = null,
  $beforeUpdateDate: Int = null, $beforePostDate: Int = null,
  $tag: String = null, $near: String = null,
  $onlyWithImage: Boolean = null, $orderMainByPostId: Boolean = null,
  $notTag: String = null
) {{
  posts(
    id: $id, city: $city, cities: $cities, authorUsername: $authorUsername,
    page: $page, limit: $limit, afterPostDate: $afterPostDate,
    afterUpdateDate: $afterUpdateDate, beforeUpdateDate: $beforeUpdateDate,
    beforePostDate: $beforePostDate, tag: $tag, near: $near,
    onlyWithImage: $onlyWithImage, orderMainByPostId: $orderMainByPostId,
    notTag: $notTag
  ) {{
    items {{ {POST_FIELDS} }}
    pageInfo {{ hasNextPage }}
  }}
}}
"""

SEARCH_POSTS = f"""
query Search(
  $search: String!, $city: String, $cities: [String],
  $authorUsername: String, $page: Int, $limit: Int,
  $tag: String, $tags: [String], $onlyWithImage: Boolean,
  $duringDate: String, $notTag: String, $hideShowRooms: Boolean,
  $orderByPostId: Boolean
) {{
  search(
    search: $search, city: $city, cities: $cities,
    authorUsername: $authorUsername, page: $page, limit: $limit,
    tag: $tag, tags: $tags, onlyWithImage: $onlyWithImage,
    duringDate: $duringDate, notTag: $notTag,
    hideShowRooms: $hideShowRooms, orderByPostId: $orderByPostId
  ) {{
    items {{ {POST_FIELDS} }}
    pageInfo {{ hasNextPage }}
  }}
}}
"""

POST_PRICES = """
query PostPricesQuery($id: [Int]) {
  postsPrice(id: $id) { postId formattedPrice inputPrice }
}
"""

POST_CONTACT = """
query PostContactQuery($postId: Int!, $isManualRequest: Boolean) {
  postContact(postId: $postId, isManualRequest: $isManualRequest) {
    contactText contactMobile shouldEnableWhatsApp
  }
}
"""

POST_VIDEOS = """
query PostsVideoQuery($id: [Int]) {
  postsVideo(id: $id) { postId videoUrl thumbUrl }
}
"""

SIMILAR_POSTS = f"""
query SimilarPosts($id: Int!, $lat: Float, $lon: Float) {{
  similarPosts(id: $id, lat: $lat, lon: $lon) {{
    id
    groupTags {{
      tag city
      posts {{
        items {{ {POST_FIELDS} }}
        pageInfo {{ hasNextPage }}
      }}
    }}
  }}
}}
"""

FAV_POSTS = f"""
query FavPostsQuery($token: String!, $limit: Int, $page: Int) {{
  favPosts(token: $token, limit: $limit, page: $page) {{
    items {{ {POST_FIELDS} }}
    pageInfo {{ hasNextPage }}
  }}
}}
"""

# ── Comments ──
GET_COMMENTS = """
query Comments(
  $postId: Int!, $commentsId: [Int!], $page: Int, $token: String,
  $newestFirst: Boolean, $oldestFirst: Boolean
) {
  comments(
    postId: $postId, id: $commentsId, page: $page, token: $token,
    newestFirst: $newestFirst, oldestFirst: $oldestFirst
  ) {
    items {
      id authorUsername authorId authorLevel body isNewUser
      status deleteReason seqId date isReply replyToCommentId
      mention { textContainsMention username handler userId }
    }
    pageInfo { hasNextPage hasPreviousPage }
  }
}
"""

SUBMIT_COMMENT = """
mutation SubmitComment($token: String!, $postId: Int!, $comment: String!, $replyToCommentId: Int) {
  submitComment(token: $token, postId: $postId, comment: $comment, replyToCommentId: $replyToCommentId) {
    status commentId notValidReason notValidReasonCode
  }
}
"""

DELETE_COMMENT = """
mutation DeleteComment($token: String!, $id: Int!, $blockCommentator: Boolean) {
  deleteComment(token: $token, id: $id, blockCommentator: $blockCommentator) {
    status notValidReason notValidReasonCode
  }
}
"""

# ── User ──
GET_USER = """
query User($token: String, $id: Int, $username: String, $handler: Handler) {
  user(token: $token, id: $id, username: $username, handler: $handler) {
    id username registrationDate countFollowers mobile handler discount
    isMember isAdmin isBlocked email didPay lastSeen messageToUser
    subscription { type joinDate expirationDate mustJoinType isActive }
    ratingSummery { upRank downRank upPaidRank downPaidRank rateAverage }
    badges { badge }
    isRealtor linkedViaNafath VATNumber
  }
}
"""

USER_RATINGS = """
query RatingsList($username: String!, $page: Int!) {
  ratings(username: $username, page: $page) {
    items { id vote rating_text buyer_name isPaid sellerFeedback date }
    pageInfo { hasNextPage hasPreviousPage }
  }
}
"""

# ── Social ──
SUBMIT_LIKE = """
mutation SubmitLike($token: String!, $id: Int!) {
  submitLike(token: $token, id: $id)
}
"""

REMOVE_LIKE = """
mutation RemoveLike($token: String!, $id: Int!) {
  removeLike(token: $token, id: $id)
}
"""

FOLLOW_USER = """
mutation FollowUser($token: String!, $username: String!) {
  followUser(token: $token, username: $username)
}
"""

UNFOLLOW_USER = """
mutation UnFollowUser($token: String!, $username: String!) {
  unFollowUser(token: $token, username: $username)
}
"""

FOLLOW_POST = """
mutation FollowPost($token: String!, $postId: Int!) {
  followPost(token: $token, id: $postId)
}
"""

FOLLOWING_USERS = """
query FollowingUsers($token: String!) {
  followingUsers(token: $token) {
    followedUsers { userId username date }
  }
}
"""

# ── Notifications ──
GET_NOTES = """
query GetNotes($token: String!, $setRead: Boolean) {
  notes(token: $token, setRead: $setRead) {
    status
    items {
      type displayTitle displayBody related_user related_ads_num
      pm_list_id pay_value thumbURL isActive tag date city url
      searchKeyword viewType
    }
  }
}
"""

# ── Locations ──
LIST_PROVINCES = """
query ListProvinces { ListProvinces { id name enName } }
"""

LIST_CITIES = """
query ListCities($provinceId: Int!) {
  ListCities(provinceId: $provinceId) { id name enName lat lon }
}
"""

LIST_NEIGHBORHOODS = """
query ListNeighborhoods($cityId: Int!) {
  ListNeighborhoods(cityId: $cityId) { id name enName lat lon }
}
"""

# ── Search helpers ──
SEARCH_SUGGEST = """
query SearchSuggest($initialChars: String!, $tag: String) {
  searchSuggest(initalChars: $initialChars, tag: $tag) { keywords }
}
"""

TAG_SUGGEST = """
query TagSuggest($keyword: String!) {
  tagSuggest(keyword: $keyword) { tags { id name } model }
}
"""

GET_FILTERS_FOR_TAGS = """
query GetFiltersForTags($tags: [String]!) {
  getFiltersForTags(tags: $tags)
}
"""

RELATED_TAGS = """
query GetRelatedTags($tag: String!, $city: String) {
  relatedTags(tag: $tag, city: $city) { tag count city }
}
"""

# ── Post management (requires auth) ──
SUBMIT_POST = """
mutation PostAd(
  $carExtraInfo: CarExtraInfo, $token: String!, $title: String!,
  $bodyTEXT: String!, $contact: String = null, $tags: [String] = null,
  $imagesList: [String] = null, $lat: Float!, $lon: Float!,
  $sec: Int = 0, $price: String = null, $recaptchaToken: String = null
) {
  submitPost(
    CarExtraInfo: $carExtraInfo, token: $token, title: $title,
    bodyTEXT: $bodyTEXT, contact: $contact, tags: $tags,
    imagesList: $imagesList, lat: $lat, lon: $lon, sec: $sec,
    price: $price, recaptchaToken: $recaptchaToken
  ) { postId notValidReason }
}
"""

DELETE_POST = """
mutation DeletePost($token: String!, $id: Int!, $reason: String) {
  deletePost(token: $token, id: $id, reason: $reason) {
    status notValidReason
  }
}
"""

UPDATE_POST = """
mutation UpdatePostMutation($token: String!, $id: Int!) {
  updatePost(token: $token, id: $id) { status notValidReason }
}
"""

POST_LIKE_INFO = """
query PostLikeInfo($id: Int!, $token: String) {
  postLikeInfo(id: $id, token: $token) { isLike isFollowing total }
}
"""
