import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Config with extended dynamic wait logic
    config = CrawlerRunConfig(
        capture_network_requests=True,
        capture_console_messages=True,

        # Wait extra time for JS or delayed network calls
        delay_before_return_html=10.0,

        # JS script to trigger lazy loading + wait for network idle
        js_code="""
            function waitForNetworkIdle(timeout = 4000) {
                return new Promise((resolve) => {
                    let lastActivity = Date.now();
                    const observer = new PerformanceObserver(() => {
                        lastActivity = Date.now();
                    });
                    observer.observe({ type: 'resource', buffered: true });

                    // Scroll to bottom to trigger all lazy loads
                    let totalHeight = 0;
                    const distance = 600;
                    const scrollInterval = setInterval(() => {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= document.body.scrollHeight) {
                            clearInterval(scrollInterval);
                        }
                    }, 500);

                    const checkIdle = setInterval(() => {
                        if (Date.now() - lastActivity > timeout) {
                            clearInterval(checkIdle);
                            observer.disconnect();
                            resolve(true);
                        }
                    }, 1000);
                });
            }
            await waitForNetworkIdle(4000);
            return true;
        """
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.mcmaster.com/products/screws/socket-head-screws-2~/alloy-steel-socket-head-screws-8/",
            config=config
        )

        if result.success:
            # --- Analyze network requests ---
            if result.network_requests:
                print(f"Captured {len(result.network_requests)} total network events")

                request_count = len([r for r in result.network_requests if r.get("event_type") == "request"])
                response_count = len([r for r in result.network_requests if r.get("event_type") == "response"])
                failed_count = len([r for r in result.network_requests if r.get("event_type") == "request_failed"])

                print(f"Requests: {request_count}, Responses: {response_count}, Failed: {failed_count}")

                # Find API calls
                api_calls = [
                    r for r in result.network_requests
                    if r.get("event_type") == "request" and "api" in r.get("url", "").lower()
                ]
                if api_calls:
                    print(f"Detected {len(api_calls)} API calls:")
                    for call in api_calls[:5]:
                        print(f"  - {call.get('method')} {call.get('url')}")

            # --- Analyze console messages ---
            if result.console_messages:
                print(f"Captured {len(result.console_messages)} console messages")

                message_types = {}
                for msg in result.console_messages:
                    msg_type = msg.get("type", "unknown")
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1

                print("Message types:", message_types)

                errors = [msg for msg in result.console_messages if msg.get("type") == "error"]
                if errors:
                    print(f"Found {len(errors)} console errors:")
                    for err in errors[:3]:
                        print(f"  - {err.get('text', '')[:100]}")

            # --- Save all captured data ---
            with open("network_capture.json", "w") as f:
                json.dump({
                    "url": result.url,
                    "network_requests": result.network_requests or [],
                    "console_messages": result.console_messages or []
                }, f, indent=2)

            print("✅ Exported detailed capture data to network_capture.json")

if __name__ == "__main__":
    asyncio.run(main())
