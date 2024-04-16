import html
import os
import feedparser
import schedule
import time
from dotenv import load_dotenv
from atproto import Client, models, client_utils
import time
import re
import typing as t
import httpx

load_dotenv()
HANDLE = os.getenv('handle')
APP_PASSWORD = os.getenv('app_password')
rss_feed = os.getenv('rss_feed')

client = Client(base_url='https://bsky.social')
client.login(HANDLE, APP_PASSWORD)

# Get the current time and subtract the desired time difference (in seconds)
days_ago = 1
hours_ago = 1
cutoff_time = time.gmtime(time.time() - 60*60*hours_ago*days_ago)

# Keep track of posted entries
posted_entries = []


_META_PATTERN = re.compile(r'<meta property="og:.*?>')
_CONTENT_PATTERN = re.compile(r'<meta[^>]+content="([^"]+)"')

def _find_tag(og_tags: t.List[str], search_tag: str) -> t.Optional[str]:
    for tag in og_tags:
        if search_tag in tag:
            return tag
    return None

def _get_tag_content(tag: str) -> t.Optional[str]:
    match = _CONTENT_PATTERN.match(tag)
    if match:
        return match.group(1)
    return None

def _get_og_tag_value(og_tags: t.List[str], tag_name: str) -> t.Optional[str]:
    tag = _find_tag(og_tags, tag_name)
    if tag:
        return _get_tag_content(tag)
    return None

def get_og_tags(url: str) -> t.Tuple[t.Optional[str], t.Optional[str], t.Optional[str]]:
    response = httpx.get(url)
    response.raise_for_status()
    og_tags = _META_PATTERN.findall(response.text)
    og_image = _get_og_tag_value(og_tags, 'og:image')
    og_title = _get_og_tag_value(og_tags, 'og:title')
    og_description = _get_og_tag_value(og_tags, 'og:description')
    return og_image, og_title, og_description

def post_without_tags(entry):
    # Extract the title and link of the entry
    title = entry.title
    link = entry.link
    # Create an AppBskyEmbedExternal object for the link
    embed_external = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            title=title,
            description='Clique para ler mais...',
            uri=link,
        )
    )
    # Post the entry with the embedded external
    client.send_post(text=title, embed=embed_external)
    # Add the entry to the list of posted entries
    posted_entries.append(entry.id)

def post_new_content():
    print('Checking for new content boss!')
    # Parse the RSS feed
    feed = feedparser.parse(rss_feed)

    for entry in feed.entries:
        try:
            # Check if the entry has been posted before and if it's more recent than the cutoff time
            if entry.id not in posted_entries and entry.published_parsed > cutoff_time:
                # Extract the title and link of the entry
                link = entry.link

                img_url, title, description = get_og_tags(link)
                if title is None or description is None:
                    print(f'Required OGP tags not found for {link}')
                    post_without_tags(entry)
                    #wait 5 minutes before posting the next entry
                    time.sleep(300)
                    continue

                thumb_blob = None
                if img_url:
                    # Download image from og:image url and upload it as a blob
                    img_data = httpx.get(img_url).content
                    thumb_blob = client.upload_blob(img_data).blob

                title = html.unescape(title)

                # AppBskyEmbedExternal is the same as "link card" in the app
                embed_external = models.AppBskyEmbedExternal.Main(
                    external=models.AppBskyEmbedExternal.External(title=title, description=description, uri=link, thumb=thumb_blob)
                )
                client.send_post(text=title, embed=embed_external)
                print(f'Posted entry: {title}')

                # Add the entry to the list of posted entries
                posted_entries.append(entry.id)

                #wait 10 mins so the feed is not overwhelmed
                time.sleep(600)

        except Exception as e:
            print(f'Error posting entry: {e}')
            continue
def main():
    # Schedule the function to run every 15 minutes
    schedule.every(1).minutes.do(post_new_content)

    print('Bot is running boss!')
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()