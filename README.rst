publishtimer Repository
========================

This project is aService for computing publish-time-recommendations.

Environment variables required:

1. `AWS_ACCESS` - AWS Access key.
2. `AWS_SECRET` - AWS Secret key.
3. `QUEUE_NAME` - The queue to read authUids from.
4. `FOLLOWERS_URL` - The url, provided by the JustUnfollow API, through which we get 5000 (max) followers of a provided `authUid`.
5. ~~`POSTS_URL` - The url, provided by the JustUnfollow API, through which we get 33 recent posts of a user based on the provided `authUid` and `instagramId`.~~
6. `API_KEY` - The api key for accessing `FOLLOWERS_URL` and POSTS_URL` securely using the JU API.
7. `HOURLY_LIMIT` - The hourly limit of accessing the number of posts every hour. This should be set well below 5000, the IG rate limit (as of this writing).
8. `INSTAGRAM_CLIENT_TOKEN` - App token for Instagram
9. `INSTAGRAM_CLIENT_SECRET` - App secret for Instagram
10. `ENCRYPTION_KEY` - For crowdfire api
11. `SERVICE` - Name of service (TAKEOFF)
12. `ACCESS_DETAILS_URL` - URL for getting access token.
13. `TWITTER_APP_KEY` - App token for Twitter
14. `TWITTER_APP_SECRET` - App secret for Twitter
15. `TW_HOURLY_LIMIT` - The hourly or 15 min limit for API. Its 180 for the user_timeline API. We have kept 100.