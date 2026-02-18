const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");

const TOKEN = process.env.WM_TOKEN || "";
const BASE_URL = (process.env.WM_BASE_URL || "http://localhost:8000/api").replace(/\/$/, "");
const WORKSPACE = process.env.WM_WORKSPACE || "admins";
const SCRIPT_ROOT = process.env.WM_SCRIPTS_ROOT || path.join(__dirname, "..", "f", "einstein_kids");
const F_ROOT = path.join(__dirname, "..", "f");

function requireEnv() {
  if (!TOKEN) {
    throw new Error("Missing WM_TOKEN. Export WM_TOKEN before running deploy_scripts.js");
  }
}

function normalizeScriptPath(filePath) {
  const rel = path.relative(F_ROOT, filePath).replace(/\\/g, "/");
  if (rel.startsWith("..")) {
    throw new Error(`Script path outside f/: ${filePath}`);
  }
  return `u/admin/${rel.replace(/\.py$/, "")}`;
}

async function upsertScript(filePath, metadataPath) {
  const code = fs.readFileSync(filePath, "utf8");
  const metadataRaw = fs.readFileSync(metadataPath, "utf8");
  const metadata = yaml.load(metadataRaw) || {};
  const scriptPath = normalizeScriptPath(filePath);

  const payload = {
    path: scriptPath,
    content: code,
    language: "python3",
    summary: metadata.summary || path.basename(filePath),
    description: metadata.description || "",
    schema: metadata.schema || {},
    kind: "script",
  };

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${TOKEN}`,
  };

  let response = await fetch(`${BASE_URL}/w/${WORKSPACE}/scripts/create`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok && response.status === 400) {
    const text = await response.text();
    if (text.toLowerCase().includes("already exists")) {
      response = await fetch(`${BASE_URL}/w/${WORKSPACE}/scripts/update/${encodeURIComponent(scriptPath)}`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
    } else {
      throw new Error(`Create failed ${scriptPath}: ${response.status} ${text}`);
    }
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Upsert failed ${scriptPath}: ${response.status} ${text}`);
  }
  console.log(`OK ${scriptPath}`);
}

async function main() {
  requireEnv();
  const folders = ["shared", "moms", "therapists"];
  for (const folder of folders) {
    const dir = path.join(SCRIPT_ROOT, folder);
    if (!fs.existsSync(dir)) {
      continue;
    }
    for (const file of fs.readdirSync(dir)) {
      if (!file.endsWith(".py")) {
        continue;
      }
      const filePath = path.join(dir, file);
      const metadataPath = filePath.replace(".py", ".script.yaml");
      if (!fs.existsSync(metadataPath)) {
        continue;
      }
      await upsertScript(filePath, metadataPath);
    }
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
