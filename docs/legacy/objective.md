You are an expert full-stack Python engineer and grocery automation architect.

### Objective
Design and implement a local automated grocery list planner and H-E-B product matcher. 
The system will:
1. Generate weekly meal plans focused strictly on Mediterranean, Mexican, and Tex-Mex cuisines.
2. Deduplicate, consolidate, and translate culinary ingredients into H-E-B store-shelf product queries.
3. Automate product lookup and cart creation on heb.com using headless browser automation.

---

### Architectural Constraints & Technical Requirements

1. **Cuisine Specifications**:
   - **Mediterranean**: EVOO, Greek yogurt, canned garbanzo beans, fresh herbs, whole grains (farro, bulgur), feta, wild-caught seafood, lean poultry, fresh citrus.
   - **Mexican / Tex-Mex**: Fresh chiles (serrano, jalapeño, poblano), cilantro, masa/corn tortillas, dry pinto/black beans, Mexican oregano, cotija, Oaxaca cheese, flank/skirt steak, avocado.
   - **H-E-B Brand Awareness**: Favor H-E-B private labels when mapping search queries:
     - `Mi Tienda` for authentic Mexican ingredients (e.g., tortillas, seasoned meats, queso fresco).
     - `H-E-B Organics` / `Central Market` for Mediterranean staples (extra virgin olive oil, organic grains, spices).
     - Standard `H-E-B` brand for staples (canned tomatoes, broth, produce).

2. **Web Scraping & Automation Strategy**:
   - `heb.com` employs client-side rendering (React/Next.js) and anti-bot protections (Akamai/Cloudflare).
   - Use **Python + Playwright** (`playwright-stealth`) or a local headless browser session.
   - Support persistent browser context (`user_data_dir`) so the user can log into their H-E-B account once, select their local store, and maintain authentication/cookies across runs.
   - Implement rate-limiting, randomized backoff delays (2–5s), and human-like scrolling.

3. **Core Modules to Generate**:
   - `config.py`: Store preferences (Store ID / Zip code), dietary parameters, pantry exclusion list (salt, pepper, tap water).
   - `planner.py`: Meal planner engine generating recipes and consolidated grocery requirements by department (Produce, Meat/Seafood, Deli/Dairy, Pantry/Grains, Spices).
   - `heb_crawler.py`: Playwright script that accepts item queries, navigates `https://www.heb.com/search/?q={query}`, captures the top in-stock matching item (name, unit price, size, product ID/URL), and optionally adds to cart or outputs a structured shopping manifest (`manifest.json` / `groceries.csv`).
   - `cli.py`: Interactive CLI to select days/servings, confirm proposed items, swap brands, and trigger the scraper.

---

### Deliverables Needed

1. **Complete Python Implementation**: Clean, production-ready, modular code for all files listed above.
2. **Setup & Run Instructions**: Playwright installation steps, browser session persistence commands, and dependency declarations (`requirements.txt`).
3. **Pantry & Staple Deduplication Logic**: A mechanism to aggregate matching units (e.g., 2 limes for dish A + 3 limes for dish B = "5 limes") and omit items already in inventory.
