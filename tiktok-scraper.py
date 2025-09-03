import os
import json
import asyncio
from dotenv import load_dotenv
from apify_client import ApifyClientAsync

# ==========================
# Load .env
# ==========================
load_dotenv()
API_TOKEN = os.getenv("APIFY_API_TOKEN")

# ==========================
# Fetch TikTok profile
# ==========================
async def fetch_tiktok_profile(apify_client, profile_url_or_name):
    actor_client = apify_client.actor("clockworks/tiktok-scraper")

    # Extract username if a URL is provided
    if "tiktok.com" in profile_url_or_name:
        username = profile_url_or_name.rstrip("/").split("@")[-1]
    else:
        username = profile_url_or_name.lstrip("@")

    input_data = {
        "profiles": [username],
        "resultsLimit": 3,
        "maxPosts": 3
    }

    call_result = await actor_client.call(run_input=input_data)
    dataset_id = call_result.get("defaultDatasetId")
    if not dataset_id:
        return None

    dataset_client = apify_client.dataset(dataset_id)

    profile_name = None
    username_val = username
    bio = "N/A"
    profile_pic = "N/A"
    post_links = []

    async for item in dataset_client.iterate_items():
        # Extract profile info once
        if not profile_name:
            author = item.get("authorMeta", {})
            username_val = author.get("uniqueId", username)
            profile_name = author.get("name", username)
            bio = author.get("signature") or author.get("bioLink") or "N/A"
            profile_pic = author.get("avatar", "N/A")

        # Collect post links
        if "webVideoUrl" in item:
            post_links.append(item["webVideoUrl"])

    return {
        "username": username_val,
        "profile_name": profile_name,
        "bio": bio,
        "profile_pic": profile_pic,
        "latest_posts": post_links[:3]
    }

# ==========================
# Save profile to JSON
# ==========================
async def save_tiktok_profile(profile_url_or_name, output_file="tiktok_profile.json"):
    apify_client = ApifyClientAsync(API_TOKEN)
    data = await fetch_tiktok_profile(apify_client, profile_url_or_name)
    if not data:
        print("❌ Failed to fetch profile data.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved TikTok profile data to {output_file}")

# ==========================
# Main
# ==========================
async def main():
    profile = "https://www.tiktok.com/@oburno0"  # or just "oburno0"
    await save_tiktok_profile(profile)

if __name__ == "__main__":
    asyncio.run(main())
