// Runs the Python planner in a background thread so the page stays responsive.
const INDEX_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
importScripts(INDEX_URL + "pyodide.js");

function today() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const ready = (async () => {
  const pyodide = await loadPyodide({ indexURL: INDEX_URL });
  const res = await fetch("py.zip");
  if (!res.ok) throw new Error(`Could not load the planner (${res.status})`);
  pyodide.unpackArchive(await res.arrayBuffer(), "zip");
  const api = pyodide.pyimport("heb_demo_api");
  api.init(today());
  return api;
})();

ready.then(
  () => postMessage({ ready: true }),
  (e) => postMessage({ failed: String(e) }),
);

onmessage = async ({ data: { id, method, path, query, body } }) => {
  try {
    const api = await ready;
    postMessage({ id, response: api.handle(method, path, query, body || "", today()) });
  } catch (e) {
    postMessage({ id, error: String(e) });
  }
};
