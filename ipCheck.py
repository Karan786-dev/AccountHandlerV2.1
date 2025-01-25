import requests
import asyncio

# List of proxies
proxies_list = """198.23.239.134:6540:unzvyaxy:ks4mxkgxyua5
207.244.217.165:6712:unzvyaxy:ks4mxkgxyua5"""

# Test URL to check IP
test_url = "http://ipinfo.io/json"

# Function to extract proxy details and check IP
def check_proxy_ip(proxy):
    # Extracting proxy details
    ip , port , username , password = proxy.split(":")
    
    # Formatting the proxy dictionary
    proxies = {
        "http": f"http://{username}:{password}@{ip}:{port}",
        "https": f"https://{username}:{password}@{ip}:{port}"
    }
    
    try:
        # Making a request through the proxy
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Proxy: {proxy} -> IP: {data['ip']}")
    except requests.RequestException as e:
        print(f"Proxy: {proxy} -> Error: {e}")

# Check IP for each proxy
async def main():
    for i in range(5):
        for proxy in proxies_list.split("\n"):
            check_proxy_ip(proxy)
        print("Completed: ",i+1)
        await asyncio.sleep(60)
        
asyncio.run(main())
