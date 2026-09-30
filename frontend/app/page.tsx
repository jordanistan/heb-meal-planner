"use client";

import { useEffect, useMemo, useState } from "react";

type Ingredient = { name: string; quantity: number; unit: string; department: string };
type Recipe = {
  id: string;
  name: string;
  cuisine: string;
  diets: string[];
  core: boolean;
  ingredients: Ingredient[];
};
type ShoppingItem = {
  ingredient: string;
  quantity: number;
  unit: string;
  department: string;
  heb_query: string;
  brand: string | null;
  deep_link: string;
  est_cost: number;
  coupon: string | null;
};
type Meal = { id: string; name: string; cuisine: string; count: number };
type Coupon = { match: string; title: string; deal: string; savings: number };
type Plan = {
  id: number | null;
  week: string;
  household_size: number;
  meal_types: string[];
  fulfillment: string;
  meals: Meal[];
  shopping_list: ShoppingItem[];
  estimated_total: number;
  budget: number | null;
  under_budget: boolean | null;
  coupons: Coupon[];
  estimated_savings: number;
};

// Diet lanes + protein-only filters, shown in one dropdown.
const DIETS: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "chicken", label: "Chicken only" },
  { value: "beef", label: "Beef only" },
  { value: "pork", label: "Pork only" },
  { value: "seafood", label: "Seafood only" },
  { value: "turkey", label: "Turkey only" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "vegan", label: "Vegan" },
  { value: "pescatarian", label: "Pescatarian" },
  { value: "gluten-free", label: "Gluten-free" },
];
const MEAL_TYPES = ["breakfast", "lunch", "dinner"];

export default function Home() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [anchors, setAnchors] = useState<Set<string>>(new Set());
  const [openId, setOpenId] = useState<string | null>(null);
  const [householdSize, setHouseholdSize] = useState(4);
  const [mealTypes, setMealTypes] = useState<Set<string>>(new Set(["lunch", "dinner"]));
  const [diet, setDiet] = useState("");
  const [budget, setBudget] = useState("");
  const [fulfillment, setFulfillment] = useState("pickup");
  const [cuisines, setCuisines] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dark, setDark] = useState(false);
  const [steps, setSteps] = useState<
    Record<string, { loading: boolean; source: string; steps: string[] }>
  >({});

  useEffect(() => {
    fetch("/api/recipes")
      .then((r) => r.json())
      .then(setRecipes)
      .catch(() => setError("Could not reach the API. Is the backend running?"));

    // Theme: honor a saved choice; otherwise follow the OS.
    let saved: string | null = null;
    try {
      saved = localStorage.getItem("theme");
    } catch {}
    const prefersDark =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-color-scheme: dark)").matches;
    const isDark = saved ? saved === "dark" : !!prefersDark;
    setDark(isDark);
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {}
  }

  const allCuisines = useMemo(
    () => Array.from(new Set(recipes.map((r) => r.cuisine))).sort(),
    [recipes],
  );

  const q = search.trim().toLowerCase();
  const showingCore = cuisines.size === 0 && q === "" && diet === "";

  const visibleRecipes = useMemo(() => {
    const DIET_TAGS = ["vegetarian", "vegan", "gluten-free"];
    const PROTEIN: Record<string, string[]> = {
      chicken: ["chicken"],
      beef: ["beef", "skirt steak", "flank steak"],
      pork: ["pork", "chorizo", "bacon", "andouille", "sausage"],
      seafood: ["salmon", "shrimp"],
      turkey: ["turkey"],
    };
    const MEAT = ["chicken", "beef", "pork", "turkey", "steak", "sausage", "chorizo", "bacon", "andouille"];
    const hasIng = (r: Recipe, kws: string[]) =>
      r.ingredients.some((i) => kws.some((k) => i.name.toLowerCase().includes(k)));
    const matchesDiet = (r: Recipe) => {
      if (!diet) return true;
      if (DIET_TAGS.includes(diet)) return r.diets.includes(diet);
      if (PROTEIN[diet]) return hasIng(r, PROTEIN[diet]);
      if (diet === "pescatarian") return !hasIng(r, MEAT);
      return r.diets.includes(diet);
    };

    return recipes.filter((r) => {
      if (showingCore) return r.core;
      if (cuisines.size && !cuisines.has(r.cuisine)) return false;
      if (!matchesDiet(r)) return false;
      if (q && !`${r.name} ${r.cuisine}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [recipes, cuisines, q, diet, showingCore]);

  function toggle(set: Set<string>, value: string): Set<string> {
    const next = new Set(set);
    next.has(value) ? next.delete(value) : next.add(value);
    return next;
  }

  async function loadSteps(id: string) {
    setSteps((s) => ({ ...s, [id]: { loading: true, source: "", steps: [] } }));
    try {
      const res = await fetch(`/api/recipes/${id}/steps`);
      const data = await res.json();
      setSteps((s) => ({
        ...s,
        [id]: { loading: false, source: data.source, steps: data.steps || [] },
      }));
    } catch {
      setSteps((s) => ({ ...s, [id]: { loading: false, source: "error", steps: [] } }));
    }
  }

  async function postPlan(anchorIds: string[] | null) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          household_size: householdSize,
          meal_types: mealTypes.size ? Array.from(mealTypes) : ["dinner"],
          diet: diet || null,
          budget: budget ? Number(budget) : null,
          fulfillment,
          cuisines: cuisines.size ? Array.from(cuisines) : null,
          anchor_meal_ids: anchorIds,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      setPlan(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function generate() {
    postPlan(anchors.size ? Array.from(anchors) : null);
  }

  function clearPlan() {
    setPlan(null);
    setError(null);
  }

  function removeMeal(id: string) {
    if (!plan) return;
    const remaining = plan.meals.filter((m) => m.id !== id).map((m) => m.id);
    if (remaining.length === 0) {
      clearPlan();
      return;
    }
    // Regenerate the consolidated list from the meals that remain.
    postPlan(remaining);
  }

  const byDepartment = useMemo(() => {
    const groups: Record<string, ShoppingItem[]> = {};
    for (const item of plan?.shopping_list ?? []) {
      (groups[item.department] ??= []).push(item);
    }
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  }, [plan]);

  return (
    <main>
      <header className="hero">
        <div>
          <h1>HEB Meal Planner</h1>
          <p>Pick your meals — get a consolidated H-E-B list, brand and all.</p>
        </div>
        <button className="themeToggle" onClick={toggleTheme} type="button">
          {dark ? "☀ Light" : "🌙 Dark"}
        </button>
      </header>

      <div className="grid">
        <section className="card">
          <h2>Your week</h2>

          <div className="row">
            <label>
              Household size
              <input
                type="number"
                min={1}
                max={12}
                value={householdSize}
                onChange={(e) => setHouseholdSize(Number(e.target.value))}
              />
            </label>
            <label>
              Diet / protein
              <select value={diet} onChange={(e) => setDiet(e.target.value)}>
                {DIETS.map((d) => (
                  <option key={d.value || "any"} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Weekly budget ($)
              <input
                type="number"
                min={0}
                placeholder="optional"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              />
            </label>
          </div>

          <h3>Meals to plan (for the week)</h3>
          <div className="chips">
            {MEAL_TYPES.map((t) => (
              <button
                key={t}
                className={mealTypes.has(t) ? "chip on" : "chip"}
                onClick={() => setMealTypes((s) => toggle(s, t))}
                type="button"
              >
                {t}
              </button>
            ))}
          </div>

          <h3>Fulfillment</h3>
          <div className="chips">
            {["pickup", "delivery"].map((f) => (
              <button
                key={f}
                className={fulfillment === f ? "chip on" : "chip"}
                onClick={() => setFulfillment(f)}
                type="button"
              >
                {f}
              </button>
            ))}
          </div>

          {allCuisines.length > 0 && (
            <>
              <h3>Cuisines</h3>
              <div className="chips">
                {allCuisines.map((c) => (
                  <button
                    key={c}
                    className={cuisines.has(c) ? "chip on" : "chip"}
                    onClick={() => setCuisines((s) => toggle(s, c))}
                    type="button"
                  >
                    {c}
                  </button>
                ))}
              </div>
            </>
          )}

          <div className="mealHead">
            <h3>Anchor meals</h3>
            <span className="count">
              {anchors.size} selected
              {anchors.size > 0 && (
                <button
                  type="button"
                  className="clear"
                  onClick={() => setAnchors(new Set())}
                >
                  clear
                </button>
              )}
            </span>
          </div>

          <p className="hint">
            {showingCore
              ? `Showing popular starters — pick a cuisine or search to see all ${recipes.length} meals. Tap a card to read the recipe.`
              : `${visibleRecipes.length} meals — tap a card to read the recipe.`}
          </p>
          <p className="hint">
            {anchors.size > 0
              ? `Your ${anchors.size} selected meal${anchors.size > 1 ? "s" : ""} will be the plan.`
              : "Select meals to build your plan, or leave empty and we'll suggest a week from your cuisines."}
          </p>

          <input
            className="mealSearch"
            type="search"
            placeholder={`Search ${recipes.length} meals…`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <div className="meals">
            {visibleRecipes.map((r) => {
              const picked = anchors.has(r.id);
              return (
                <div
                  key={r.id}
                  className={picked ? "mcard picked" : "mcard"}
                  onClick={() => setOpenId(r.id)}
                >
                  <input
                    type="checkbox"
                    className="pick"
                    checked={picked}
                    onClick={(e) => e.stopPropagation()}
                    onChange={() => setAnchors((s) => toggle(s, r.id))}
                    aria-label={`Add ${r.name}`}
                  />
                  <span className="mname">{r.name}</span>
                  <em>
                    {r.cuisine}
                    {r.diets.length ? ` · ${r.diets.join(", ")}` : ""}
                  </em>
                  <span className="hintTap">
                    {picked ? "✓ added · tap to view" : "tap to view"}
                  </span>
                </div>
              );
            })}
            {visibleRecipes.length === 0 && (
              <p className="muted">No meals match that search.</p>
            )}
          </div>

          <button className="primary" onClick={generate} disabled={loading}>
            {loading ? "Building your plan…" : "Generate plan"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="card">
          <div className="planHead">
            <h2>This week&apos;s plan</h2>
            {plan && (
              <button type="button" className="clear" onClick={clearPlan}>
                clear plan
              </button>
            )}
          </div>
          {!plan && <p className="muted">Your plan and shopping list will appear here.</p>}

          {plan && (
            <>
              <div className="totals">
                <span className="total">${plan.estimated_total.toFixed(2)}</span>
                {plan.budget != null && (
                  <span className={plan.under_budget ? "budgetTag ok" : "budgetTag over"}>
                    {plan.under_budget ? "under" : "over"} ${plan.budget.toFixed(0)} budget
                  </span>
                )}
              </div>
              <p className="estNote">
                Estimated cart total · {plan.household_size} people ·{" "}
                {plan.meal_types.join(" + ")} · {plan.meals.reduce((n, m) => n + m.count, 0)}{" "}
                meals · for {plan.fulfillment}. Prices are estimates.
              </p>

              {plan.coupons.length > 0 && (
                <div className="deals">
                  <h4>This week&apos;s H-E-B deals on your list</h4>
                  <ul>
                    {plan.coupons.map((c) => (
                      <li key={c.match}>
                        {c.title}: {c.deal}{" "}
                        <span className="save">(save ~${c.savings.toFixed(2)})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <ul className="mealList">
                {plan.meals.map((m) => (
                  <li key={m.id}>
                    <span>
                      {m.name} <span className="tag">{m.cuisine}</span>
                      {m.count > 1 && <span className="times">×{m.count}</span>}
                    </span>
                    <button
                      type="button"
                      className="removeMeal"
                      onClick={() => removeMeal(m.id)}
                      aria-label={`Remove ${m.name}`}
                      title="Remove from plan"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>

              <h3>Shopping list</h3>
              {byDepartment.map(([dept, items]) => (
                <div key={dept} className="dept">
                  <h4>{dept}</h4>
                  {items.map((item) => (
                    <a
                      key={item.ingredient}
                      className="item"
                      href={item.deep_link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span className="qty">
                        {item.quantity} {item.unit}
                      </span>
                      <span className="name">
                        {item.ingredient}
                        {item.brand && <span className="brand">{item.brand}</span>}
                        {item.coupon && <span className="deal">{item.coupon}</span>}
                      </span>
                      <span className="cost">${item.est_cost.toFixed(2)}</span>
                      <span className="go">Find →</span>
                    </a>
                  ))}
                </div>
              ))}
            </>
          )}
        </section>
      </div>

      {openId &&
        (() => {
          const r = recipes.find((x) => x.id === openId);
          if (!r) return null;
          const picked = anchors.has(r.id);
          const st = steps[r.id];
          return (
            <div className="modalBackdrop" onClick={() => setOpenId(null)}>
              <div
                className="modalPanel"
                role="dialog"
                aria-modal="true"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  className="modalClose"
                  onClick={() => setOpenId(null)}
                  aria-label="Close"
                >
                  ×
                </button>
                <h3 className="modalTitle">{r.name}</h3>
                <p className="modalSub">
                  {r.cuisine}
                  {r.diets.length ? ` · ${r.diets.join(", ")}` : ""}
                </p>

                <h4>Ingredients</h4>
                <ul className="modalIng">
                  {r.ingredients.map((i) => (
                    <li key={i.name}>
                      {i.quantity} {i.unit} {i.name}
                    </li>
                  ))}
                </ul>

                <h4>Cooking steps</h4>
                {!st && (
                  <button
                    type="button"
                    className="stepsBtn"
                    onClick={() => loadSteps(r.id)}
                  >
                    + Generate cooking steps
                  </button>
                )}
                {st?.loading && <p className="muted">Generating steps…</p>}
                {st && !st.loading && st.source === "unavailable" && (
                  <p className="muted">Set an API key to generate steps.</p>
                )}
                {st && !st.loading && st.steps.length > 0 && (
                  <ol className="modalSteps">
                    {st.steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                )}

                <div className="modalActions">
                  <button
                    type="button"
                    className={picked ? "add on" : "add"}
                    onClick={() => setAnchors((s) => toggle(s, r.id))}
                  >
                    {picked ? "✓ Added to plan" : "Add to plan"}
                  </button>
                </div>
              </div>
            </div>
          );
        })()}
    </main>
  );
}
