import httpx
import asyncio

async def test():
    url = "https://10.0.0.14"
    api_key = "3-4vPYKNTxvN9BymmhgU77JDvrQBPbOdkCr7oM7n7ODScoZA7xaiKM1Al6uNNlKldS"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.get(f"{url}/api/v2.0/system/info", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ API Key is valid!")
                print(response.json())
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")

asyncio.run(test())
