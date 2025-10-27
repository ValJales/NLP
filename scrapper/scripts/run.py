from pathlib import Path
import asyncio
import json
import csv
import twitter
import os
import re
from loguru import logger
from scrapfly import ScrapeConfig

output = Path(__file__).parent / "results"
output.mkdir(exist_ok=True)

# On teste avec le Macron (fdp)
french_politicians = {
    'EmmanuelMacron': 'center',  # Emmanuel Macron (LREM)
}

async def scrape_politician_tweets(username, political_affiliation, tweets_per_politician=30):
    """On scrape les tweets d'un profil de politicien"""
    try:
        # D'abort on récupère la page de profil pour extraire les IDs des tweets
        url = f"https://twitter.com/{username}"
        logger.info(f"Scraping timeline for {username}")
        
        # On modifie l'approche de scraping pour mieux trouver les tweets
        timeline_result = await twitter.SCRAPFLY.async_scrape(
            ScrapeConfig(
                url=url,
                auto_scroll=True,
                wait_for_selector="[data-testid='tweet']",
                **twitter.BASE_CONFIG
            )
        )
        
        # On extrait les IDs de tweets en utilisant plusieurs expressions régulières
        content = timeline_result.content
        
        # Save HTML for debugging
        debug_file = output / f"{username}_timeline.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved timeline HTML to {debug_file} for debugging")
        
        # On essaie different patterns
        tweet_ids = []
        
        # Pattern 1: Standard pattern
        pattern1 = fr'twitter\.com/{username}/status/(\d+)'
        matches1 = re.findall(pattern1, content)
        tweet_ids.extend(matches1)
        
        # Pattern 2: URL encoded pattern
        pattern2 = fr'twitter\.com\/{username}\/status\/(\d+)'
        matches2 = re.findall(pattern2, content)
        tweet_ids.extend(matches2)
        
        # Pattern 3: X.com pattern
        pattern3 = fr'x\.com/{username}/status/(\d+)'
        matches3 = re.findall(pattern3, content)
        tweet_ids.extend(matches3)
        
        # Pattern 4: Look for data attributes
        pattern4 = r'data-tweet-id="(\d+)"'
        matches4 = re.findall(pattern4, content)
        tweet_ids.extend(matches4)
        
        # Pattern 5: Look for any status ID 
        pattern5 = r'/status/(\d+)'
        matches5 = re.findall(pattern5, content)
        tweet_ids.extend(matches5)
        
        # Remove duplicates and limit to requested number
        tweet_ids = list(dict.fromkeys(tweet_ids))[:tweets_per_politician]
        
        logger.info(f"Found {len(tweet_ids)} tweet IDs for {username}")
        logger.info(f"First few IDs: {tweet_ids[:5]}")
        
        if not tweet_ids:
            logger.error("No tweet IDs found. Check the HTML structure.")
            return []
        
        # Now scrape each tweet
        tweets_data = []
        for i, tweet_id in enumerate(tweet_ids):
            try:
                tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                logger.info(f"Scraping tweet {i+1}/{len(tweet_ids)}: {tweet_url}")
                
                tweet_data = await twitter.scrape_tweet(tweet_url)
                
                # Create a simple tweet record with just the essential information
                tweet_record = {
                    'username': username,
                    'political_affiliation': political_affiliation,
                    'text': tweet_data.get('text', ''),
                    'created_at': tweet_data.get('created_at', ''),
                    'id': tweet_data.get('id', '')
                }
                
                tweets_data.append(tweet_record)
                logger.info(f"Successfully scraped tweet: {tweet_record['text'][:50]}...")
                
                # Don't hammer the API
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping tweet {tweet_id}: {e}")
        
        return tweets_data
    
    except Exception as e:
        logger.error(f"Error scraping tweets for {username}: {e}")
        return []

async def run():
    twitter.BASE_CONFIG["debug"] = True  # Enable debug mode
    
    all_tweets = []
    
    # Create a CSV file to write tweets as we go
    csv_file = output / "politician_tweets.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['username', 'political_affiliation', 'text', 'created_at', 'id']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each politician
        for username, political_affiliation in french_politicians.items():
            try:
                logger.info(f"Scraping tweets for {username} ({political_affiliation})...")
                
                tweets = await scrape_politician_tweets(username, political_affiliation)
                
                if tweets:
                    # Write tweets to CSV file
                    for tweet in tweets:
                        writer.writerow(tweet)
                    
                    # Add to all tweets
                    all_tweets.extend(tweets)
                    
                    logger.info(f"Successfully scraped {len(tweets)} tweets for {username}")
                else:
                    logger.warning(f"No tweets found for {username}")
                
                # Wait between politicians to avoid rate limiting
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error processing {username}: {e}")
    
    logger.info(f"Completed scraping {len(all_tweets)} tweets from {len(french_politicians)} politicians")
    logger.info(f"Results saved to {csv_file}")

if __name__ == "__main__":
    asyncio.run(run())