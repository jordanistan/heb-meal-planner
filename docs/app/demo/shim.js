// Loaded before the app. Sends the app's /api calls to the in-browser planner
// instead of a server, so the unmodified UI runs on static hosting.
(function () {
  const here = document.currentScript.src.replace(/[^/]*$/, "");
  const worker = new Worker(here + "worker.js");
  const pending = new Map();
  let nextId = 1;

  // The app restores its last plan by id, but demo plans only live until reload.
  try {
    localStorage.removeItem("planId");
  } catch {}

  const css = document.createElement("style");
  css.textContent = `
    html{padding-bottom:64px}
    #demo-bar{position:fixed;left:0;right:0;bottom:0;z-index:9000;padding:10px 16px;background:#16181d;color:#fff;
      font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;text-align:center}
    #demo-bar a{color:#ffb4ae}
    #demo-load{position:fixed;inset:0;z-index:9001;display:flex;flex-direction:column;align-items:center;justify-content:center;
      gap:10px;padding:24px;background:#b3121d;color:#fff;text-align:center;font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
    #demo-load h1{margin:0;font-size:34px;color:#fff}
    #demo-load p{margin:0;font-size:18px}
    #demo-load a{color:#fff}
  `;
  document.documentElement.appendChild(css);

  const bar = document.createElement("div");
  bar.id = "demo-bar";
  bar.innerHTML =
    'Demo with sample prices and deals. Everything stays in your browser and resets when you reload. <a href="../">Back to the overview</a>';
  const load = document.createElement("div");
  load.id = "demo-load";
  load.innerHTML = "<h1>HEB Meal Planner</h1><p>Starting the demo. This can take a few seconds the first time.</p>";
  document.documentElement.append(bar, load);

  worker.onmessage = ({ data }) => {
    if (data.ready) {
      load.remove();
      return;
    }
    if (data.failed) {
      load.innerHTML =
        '<h1>The demo could not start</h1><p>Please reload the page, or <a href="../#tour">watch the video tour</a> instead.</p>';
      console.error("Demo failed to start:", data.failed);
      return;
    }
    const call = pending.get(data.id);
    if (!call) return;
    pending.delete(data.id);
    data.error ? call.reject(new Error(data.error)) : call.resolve(JSON.parse(data.response));
  };

  function callApi(url, method, body) {
    return new Promise((resolve, reject) => {
      const id = nextId++;
      pending.set(id, { resolve, reject });
      worker.postMessage({
        id,
        method,
        path: url.pathname.slice("/api".length),
        query: url.search.slice(1),
        body: body || "",
      });
    });
  }

  const isApi = (url) => url.origin === location.origin && url.pathname.startsWith("/api/");

  const realFetch = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    const raw = typeof input === "string" || input instanceof URL ? String(input) : input.url;
    const url = new URL(raw, location.href);
    if (!isApi(url)) return realFetch(input, init);
    try {
      const out = await callApi(url, (init && init.method) || "GET", init && init.body);
      return new Response(out.status === 204 ? null : out.body, {
        status: out.status,
        headers: { "content-type": out.type },
      });
    } catch (e) {
      console.error(e);
      return Response.json({ detail: "The demo hit a problem. Please reload." }, { status: 500 });
    }
  };

  // Report links would otherwise navigate to a server route that doesn't exist.
  document.addEventListener(
    "click",
    (event) => {
      const link = event.target.closest && event.target.closest('a[href^="/api/"]');
      if (!link) return;
      event.preventDefault();
      event.stopPropagation();
      const url = new URL(link.href);
      const asFile = url.searchParams.has("download") || url.searchParams.get("format") === "csv";
      // Opened during the click so popup blockers allow it.
      const tab = asFile ? null : window.open("", "_blank");
      callApi(url, "GET").then((out) => {
        if (out.status !== 200) {
          if (tab) tab.close();
          console.error("Report failed:", out.body);
          return;
        }
        const blobUrl = URL.createObjectURL(new Blob([out.body], { type: out.type }));
        if (tab) {
          tab.location.href = blobUrl;
        } else {
          const save = document.createElement("a");
          save.href = blobUrl;
          save.download = out.filename;
          save.click();
        }
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
      });
    },
    true,
  );
})();
