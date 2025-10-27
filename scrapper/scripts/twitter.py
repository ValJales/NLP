"""
Pour lancer ce scraper, définissez la variable d'environnement $SCRAPFLY_KEY avec votre clé d'API scrapfly:
$ export $SCRAPFLY_KEY="votre clé de https://scrapfly.io/dashboard"
"""

import json
import os
import jmespath

from typing import Dict

from loguru import logger as log
from scrapfly import ScrapeConfig, ScrapflyClient

SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])
BASE_CONFIG = {
    "asp": True,
    "render_js": True,
}


async def _scrape_twitter_app(url: str, _retries: int = 0, **scrape_config) -> Dict:
    """On scrape la page Twitter et on scroll jusqu'à la fin de la page si possible"""
    if not _retries:
        log.info("scraping {}", url)
    else:
        log.info("retrying {}/2 {}", _retries, url)
    result = await SCRAPFLY.async_scrape(
        ScrapeConfig(url, auto_scroll=True, lang=["en-US"], **scrape_config, **BASE_CONFIG)
    )
    if "Something went wrong, but" in result.content:
        if _retries > 2:
            raise Exception("Twitter web app crashed too many times")
        return await _scrape_twitter_app(url, _retries=_retries + 1, **scrape_config)
    return result


def parse_tweet(data: Dict) -> Dict:
    """On parse les données JSON du tweet pour extraire les champs les plus importants"""
    result = jmespath.search(
        """{
        created_at: legacy.created_at,
        attached_urls: legacy.entities.urls[].expanded_url,
        attached_urls2: legacy.entities.url.urls[].expanded_url,
        attached_media: legacy.entities.media[].media_url_https,
        tagged_users: legacy.entities.user_mentions[].screen_name,
        tagged_hashtags: legacy.entities.hashtags[].text,
        favorite_count: legacy.favorite_count,
        bookmark_count: legacy.bookmark_count,
        quote_count: legacy.quote_count,
        reply_count: legacy.reply_count,
        retweet_count: legacy.retweet_count,
        quote_count: legacy.quote_count,
        text: legacy.full_text,
        is_quote: legacy.is_quote_status,
        is_retweet: legacy.retweeted,
        language: legacy.lang,
        user_id: legacy.user_id_str,
        id: legacy.id_str,
        conversation_id: legacy.conversation_id_str,
        source: source,
        views: views.count
    }""",
        data,
    )
    result["poll"] = {}
    poll_data = jmespath.search("card.legacy.binding_values", data) or []
    for poll_entry in poll_data:
        key, value = poll_entry["key"], poll_entry["value"]
        if "choice" in key:
            result["poll"][key] = value["string_value"]
        elif "end_datetime" in key:
            result["poll"]["end"] = value["string_value"]
        elif "last_updated_datetime" in key:
            result["poll"]["updated"] = value["string_value"]
        elif "counts_are_final" in key:
            result["poll"]["ended"] = value["boolean_value"]
        elif "duration_minutes" in key:
            result["poll"]["duration"] = value["string_value"]
    user_data = jmespath.search("core.user_results.result", data)
    if user_data:
        result["user"] = parse_profile(user_data)
    return result


async def scrape_tweet(url: str) -> Dict:
    """
    On scrape une page de tweet unique pour un fil de discussion de tweet par exemple:
    https://twitter.com/Scrapfly_dev/status/1667013143904567296
    Retourne le tweet parent, les tweets de réponse et les tweets recommandés
    """
    result = await _scrape_twitter_app(url, wait_for_selector="[data-testid='tweet']")
    _xhr_calls = result.scrape_result["browser_data"]["xhr_call"]
    tweet_call = [f for f in _xhr_calls if "TweetResultByRestId" in f["url"]]
    for xhr in tweet_call:
        if not xhr["response"]:
            continue
        data = json.loads(xhr["response"]["body"])
        return parse_tweet(data['data']['tweetResult']['result'])


def parse_profile(data: Dict) -> Dict:
    """On parse X.com (Twitter) user profile JSON dataset en une structure plate"""
    return {"id": data["id"], "rest_id": data["rest_id"], "verified": data["is_blue_verified"], **data["legacy"]}


async def scrape_profile(url: str) -> Dict:
    """
    On scrape X.com (Twitter) la page de profil de l'utilisateur par exemple:
    https://x.com/scrapfly_dev
    Retourne les données de l'utilisateur et les derniers tweets
    """
    result = await _scrape_twitter_app(url, wait_for_selector="[data-testid='primaryColumn']")
    _xhr_calls = result.scrape_result["browser_data"]["xhr_call"]
    user_calls = [f for f in _xhr_calls if "UserBy" in f["url"]]
    for xhr in user_calls:
        data = json.loads(xhr["response"]["body"])
        parsed = parse_profile(data["data"]["user"]["result"])
        return parsed
    raise Exception("Failed to scrape user profile - no matching user data background requests")