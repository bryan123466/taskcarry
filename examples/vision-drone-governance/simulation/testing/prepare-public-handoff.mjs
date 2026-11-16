import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, realpath, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

// Resolve this public layout locally. Preserve recorded evidence and all verifier assertions.
const testing = path.dirname(fileURLToPath(import.meta.url));
const root = await realpath(path.join(testing, ".."));
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const readJSON = async name => JSON.parse((await readFile(path.join(root, name), "utf8")).replace(/^\uFEFF/, ""));
const manifest = await readJSON("case-manifest.json");
for (const entry of manifest.files) {
  assert(!path.isAbsolute(entry.path) && !entry.path.split(/[\\/]/).includes(".."));
  const file = await realpath(path.join(root, entry.path));
  assert(file.startsWith(root + path.sep), "File escaped example root");
  assert.equal(sha(await readFile(file)), entry.sha256, "Changed public file: " + entry.path);
}
const local = path.join(testing, "local");
await mkdir(local, { recursive: true });
const runInput = await mkdtemp(path.join(local, "handoff-"));
const algorithm = await readJSON("algorithm/algorithm-evidence.json");
for (const name of ["detector.js", "controller.js"]) {
  algorithm.files[name].path = path.join(root, "app", name);
  assert.equal(sha(await readFile(algorithm.files[name].path)), algorithm.files[name].sha256);
}
algorithm.contract.path = path.join(root, "INTERFACE_CONTRACT.json");
algorithm.export_metadata.local_adapter = "Only paths resolved for this local run; observations unchanged.";
const algorithmPath = path.join(runInput, "algorithm-evidence.json");
await writeFile(algorithmPath, JSON.stringify(algorithm, null, 2) + "\n", { flag: "wx" });
const software = await readJSON("software-evidence.json");
const appHashes = Object.fromEntries(Object.entries(software.file_sha256)
  .filter(([name]) => name.startsWith("app/")).map(([name, hash]) => [name.slice(4), hash]));
const handoff = {
  contract_sha256: software.contract_sha256,
  app_directory: path.join(root, "app"), app_sha256: appHashes,
  software_evidence: { path: path.join(root, "software-evidence.json"), sha256: sha(await readFile(path.join(root, "software-evidence.json"))) },
  algorithm_evidence: { path: algorithmPath, sha256: sha(await readFile(algorithmPath)) },
  supporting_sha256: Object.fromEntries(await Promise.all(["SOFTWARE_RUN.md", "verify-software.mjs"]
    .map(async name => [name, sha(await readFile(path.join(root, name)))])))
};
const handoffPath = path.join(runInput, "handoff.json");
await writeFile(handoffPath, JSON.stringify(handoff, null, 2) + "\n", { flag: "wx" });
const child = spawn(process.execPath, [path.join(testing, "verify-independent.mjs"), handoffPath], {
  cwd: root, stdio: "inherit", windowsHide: true
});
child.on("error", error => { console.error(error); process.exitCode = 1; });
child.on("exit", code => { process.exitCode = code ?? 1; });
