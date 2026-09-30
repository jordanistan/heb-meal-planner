This implementation uses the official `mcp` Python SDK (`mcp.server.fastmcp`) paired with Playwright to expose H-E-B product searches directly as tools inside Claude Desktop.

### Project Directory Structure

```text
heb-mcp-server/
├── server.py
├── requirements.txt
└── heb_user_data/        # Persistent browser profile (created on first run)

```

---

### 1. Dependencies (`requirements.txt`)

```text
mcp>=1.0.0
playwright>=1.49.0
playwright-stealth>=1.0.6
pydantic>=2.0.0

```

Install dependencies and set up the browser binaries:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

```

---

### 2. FastMCP Server Implementation (`server.py`)

Save the following file in your project directory. It launches a persistent Chromium context so your store selection and session cookies persist across Claude Desktop queries.

```python
#!/usr/bin/env python3
import asyncio
import os
import urllib.parse
from typing import List, Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

mcp = FastMCP("HEB Grocery Engine")

# Base directory for persistent session/cookies
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "heb_user_data")


class HEBProduct(BaseModel):
    product_id: Optional[str] = Field(None, description="H-E-B SKU or unique ID")
    title: str = Field(..., description="Item title as listed on shelf")
    brand: Optional[str] = Field(None, description="Brand name (e.g., Mi Tienda, H-E-B Organics)")
    price: Optional[str] = Field(None, description="Current price string (e.g., $3.48)")
    unit_price: Optional[str] = Field(None, description="Unit price (e.g., $0.22/oz)")
    in_stock: bool = Field(True, description="Stock status")
    product_url: Optional[str] = Field(None, description="Direct URL to product")


async def search_heb_playwright(query: str, max_results: int = 5) -> List[dict]:
    """Headless automated search using Playwright with persistent context."""
    results = []
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.heb.com/search/?q={encoded_query}"

    async with async_playwright() as p:
        # Launch persistent context to reuse store selection and bypass repeated bot challenges
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
            ],
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        )

        page = await context.new_page()
        await stealth_async(page)

        try:
            # Navigate to search query
            await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2500)  # Grace period for hydration

            # Select product cards from DOM
            product_cards = await page.query_selector_all('[data-testid="product-card"], [class*="ProductCard"]')
            
            for card in product_cards[:max_results]:
                title_elem = await card.query_selector('[data-testid="product-title"], [class*="productTitle"], h2, h3')
                price_elem = await card.query_selector('[data-testid="product-price"], [class*="price"]')
                unit_price_elem = await card.query_selector('[class*="uom"], [class*="unitPrice"]')
                link_elem = await card.query_selector('a[href*="/product-detail/"]')

                title = (await title_elem.inner_text()).strip() if title_elem else "Unknown Product"
                price = (await price_elem.inner_text()).strip() if price_elem else None
                unit_price = (await unit_price_elem.inner_text()).strip() if unit_price_elem else None
                
                href = await link_elem.get_attribute("href") if link_elem else None
                full_url = f"https://www.heb.com{href}" if href and href.startswith("/") else href

                # Determine if out of stock
                card_text = (await card.inner_text()).lower()
                is_in_stock = "out of stock" not in card_text and "temporarily unavailable" not in card_text

                # Brand categorization helper
                brand = None
                for candidate in ["Mi Tienda", "Central Market", "H-E-B Organics", "H-E-B", "Hill Country Fare"]:
                    if candidate.lower() in title.lower():
                        brand = candidate
                        break

                results.append({
                    "title": title,
                    "brand": brand,
                    "price": price,
                    "unit_price": unit_price,
                    "in_stock": is_in_stock,
                    "product_url": full_url,
                })
        finally:
            await context.close()

    return results


@mcp.tool()
async def search_heb_products(query: str, max_results: int = 5) -> str:
    """
    Search H-E-B catalog for a specific grocery item.
    
    Args:
        query: Search term (e.g., 'Mi Tienda arrachera', 'Greek extra virgin olive oil', 'poblano peppers')
        max_results: Max items to return (default: 5)
    """
    try:
        items = await search_heb_playwright(query=query, max_results=max_results)
        if not items:
            return f"No results found on H-E-B for '{query}'."

        formatted_output = [f"Found {len(items)} results for '{query}':"]
        for idx, item in enumerate(items, 1):
            stock_str = "In Stock" if item["in_stock"] else "Out of Stock"
            brand_str = f" [{item['brand']}]" if item["brand"] else ""
            formatted_output.append(
                f"{idx}. {item['title']}{brand_str}\n"
                f"   Price: {item['price'] or 'N/A'} ({item['unit_price'] or 'unit price unavailable'})\n"
                f"   Availability: {stock_str}\n"
                f"   Link: {item['product_url'] or 'N/A'}"
            )
        return "\n\n".join(formatted_output)
    except Exception as e:
        return f"Error executing search for '{query}': {str(e)}"


@mcp.tool()
def map_cuisine_ingredient_to_heb_query(ingredient: str, cuisine: str) -> str:
    """
    Translates general culinary recipe ingredients (Mediterranean, Mexican, Tex-Mex) 
    into optimized H-E-B search terms and preferred brand lines.
    """
    lookup = {
        # Mexican / Tex-Mex
        "fajita beef": "Mi Tienda Seasoned Beef Fajitas",
        "arrachera": "Mi Tienda Seasoned Beef Fajitas Inside Skirt",
        "skirt steak": "beef skirt steak",
        "flank steak": "beef flank steak",
        "queso fresco": "Mi Tienda Queso Fresco",
        "oaxaca cheese": "Mi Tienda Queso Oaxaca",
        "cotija": "Mi Tienda Cotija Grated Cheese",
        "corn tortillas": "Mi Tienda Ready to Cook Corn Tortillas",
        "flour tortillas": "H-E-B Bakery Fresh Butter Tortillas",
        "chorizo": "Mi Tienda Mexican Pork Chorizo",
        "poblano": "Fresh Poblano Peppers",
        "serrano": "Fresh Serrano Peppers",
        "mexican oregano": "Mi Tienda Mexican Oregano",
        "cilantro": "Fresh Cilantro Bunch",
        "black beans": "H-E-B Seasoned Black Beans with Jalapeno",
        "pinto beans": "H-E-B Charro Beans with Bacon",
        
        # Mediterranean
        "olive oil": "Central Market Extra Virgin Olive Oil PDO Kalamata",
        "feta": "Central Market Greek Feta Cheese in Brine",
        "greek yogurt": "Central Market Organic Plain Greek Whole Milk Yogurt",
        "farro": "Central Market Organic Farro",
        "bulgur": "Central Market Organic Bulgur Wheat",
        "tahini": "Central Market Organic Sesame Tahini",
        "chickpeas": "H-E-B Organics Garbanzo Beans",
        "canned tomatoes": "H-E-B Organics Diced Tomatoes",
        "kalamata olives": "Central Market Pitted Kalamata Olives",
        "capers": "Central Market Non-Pareil Capers in Brine",
    }
    
    key = ingredient.lower().strip()
    for pattern, heb_term in lookup.items():
        if pattern in key:
            return f"Optimal search query for {ingredient} ({cuisine}): '{heb_term}'"
            
    # Default fallback heuristics
    if cuisine.lower() in ["mexican", "tex-mex"]:
        return f"Suggested query: 'Mi Tienda {ingredient}' or 'H-E-B {ingredient}'"
    elif cuisine.lower() == "mediterranean":
        return f"Suggested query: 'Central Market {ingredient}' or 'H-E-B Organics {ingredient}'"
    return f"Suggested query: 'H-E-B {ingredient}'"


if __name__ == "__main__":
    mcp.run(transport="stdio")

```

---

### 3. One-Time Setup: Set Your Store Location

H-E-B requires a physical store selection to show accurate stock and local pricing. Launch Chromium interactively once into the same `heb_user_data` directory:

```bash
source .venv/bin/activate
playwright launch --persistent-context ./heb_user_data --viewport-size 1280,800 https://www.heb.com

```

1. Click **Select Store** in the top navigation and enter your zip code or local H-E-B location.
2. (Optional) Log into your H-E-B account if you want digital coupons and cart syncing.
3. Close the browser window. The context is now saved in `./heb_user_data`.

---

### 4. Claude Desktop Configuration

Add the server to your `claude_desktop_config.json`:

* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Linux**: `~/.config/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "heb-grocery": {
      "command": "/ABSOLUTE/PATH/TO/heb-mcp-server/.venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/heb-mcp-server/server.py"
      ]
    }
  }
}

```

*(On Windows, use backslashes escaped as `\\\\` and target `python.exe` inside `.venv\\Scripts`).*

---

### 5. Testing the Integration

Restart Claude Desktop. You will see a hammer/tool icon indicating `HEB Grocery Engine` is active with two tools:

* `search_heb_products`
* `map_cuisine_ingredient_to_heb_query`

You can prompt Claude directly:

> *"Plan a 3-day Tex-Mex and Mediterranean dinner plan, then search H-E-B for the exact Mi Tienda and Central Market items I need to buy."*

Claude will normalize each ingredient using the translation layer and invoke the Playwright scraper in the background to return live store prices, stock status, and product links directly in chat.
