/**
 * Скачивает Python wheels с PyPI для офлайн-установки.
 * node scripts/download-wheels.mjs
 */
import https from "https";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WHEELS_DIR = path.join(__dirname, "..", "wheels");

const PACKAGES = [
  "fastapi==0.115.6",
  "uvicorn==0.34.0",
  "starlette==0.41.3",
  "sqlalchemy==2.0.36",
  "greenlet==3.1.1",
  "aiosqlite==0.20.0",
  "pydantic==2.10.3",
  "pydantic-core==2.27.1",
  "pydantic-settings==2.6.1",
  "python-dotenv",
  "python-jose==3.3.0",
  "passlib==1.7.4",
  "bcrypt==4.2.1",
  "python-multipart==0.0.20",
  "pypdf==5.1.0",
  "python-docx==1.1.2",
  "openpyxl==3.1.5",
  "beautifulsoup4==4.12.3",
  "aiofiles==24.1.0",
  "email-validator==2.2.0",
  "httpx==0.28.1",
  "anyio==4.7.0",
  "httpcore==1.0.7",
  "h11==0.14.0",
  "certifi",
  "idna",
  "sniffio",
  "typing-extensions",
  "annotated-types",
  "click",
  "colorama",
  "lxml",
  "soupsieve",
  "et-xmlfile",
  "ecdsa",
  "six",
  "rsa",
  "pyasn1",
  "cryptography",
  "cffi",
  "pycparser",
  "dnspython",
];

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "expert17025-setup" } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return get(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
      res.on("error", reject);
    }).on("error", reject);
  });
}

function pickWheel(urls) {
  const wheels = urls.filter((u) => u.filename?.endsWith(".whl"));
  const win312 = wheels.find((u) => u.filename.includes("cp312") && u.filename.includes("win_amd64"));
  if (win312) return win312;
  const winAny = wheels.find((u) => u.filename.includes("win_amd64"));
  if (winAny) return winAny;
  const universal = wheels.find((u) => u.filename.includes("py3-none-any") || u.filename.includes("py2.py3-none-any"));
  if (universal) return universal;
  const abi = wheels.find((u) => u.filename.includes("abi3") && !u.filename.includes("macosx"));
  if (abi) return abi;
  return wheels[0];
}

async function downloadPackage(spec) {
  const [name, version] = spec.includes("==") ? spec.split("==") : [spec, null];
  const url = version
    ? `https://pypi.org/pypi/${name}/${version}/json`
    : `https://pypi.org/pypi/${name}/json`;
  const data = JSON.parse((await get(url)).toString());
  const ver = version || data.info.version;
  const release = data.releases?.[ver] || data.urls || [];
  const wheel = pickWheel(release);
  if (!wheel) {
    console.log(`  ⚠ нет wheel: ${name}==${ver}`);
    return false;
  }
  const dest = path.join(WHEELS_DIR, wheel.filename);
  if (fs.existsSync(dest)) {
    console.log(`  ✓ есть: ${wheel.filename}`);
    return true;
  }
  console.log(`  ↓ ${wheel.filename}`);
  const buf = await get(wheel.url);
  fs.writeFileSync(dest, buf);
  return true;
}

async function main() {
  fs.mkdirSync(WHEELS_DIR, { recursive: true });
  console.log("Скачивание wheels в", WHEELS_DIR);
  for (const pkg of PACKAGES) {
    try {
      await downloadPackage(pkg);
    } catch (e) {
      console.log(`  ✗ ${pkg}: ${e.message}`);
    }
  }
  const count = fs.readdirSync(WHEELS_DIR).filter((f) => f.endsWith(".whl")).length;
  console.log(`\nГотово: ${count} wheels`);
}

main();
