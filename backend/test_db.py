import os
import requests # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Testing connection to: {url}...")

try:
    # We ping the health check endpoint
    response = requests.get(
        f"{url}/rest/v1/", 
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=5
    )
    if response.status_code == 200:
        print("✅ SUCCESS! Your computer can talk to Supabase.")
    else:
        print(f"⚠️ Reached Supabase, but got error: {response.status_code}")
except Exception as e:
    print(f"❌ FAILED to connect: {e}")