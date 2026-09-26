// Kontratları derler: node compile.js  →  build/<Kontrat>.json (abi + bytecode)
// Gerekli: npm install  (package.json içindeki solc paketi)
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const dir = path.join(__dirname, "contracts");
const sources = {};
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith(".sol"))) {
  sources[f] = { content: fs.readFileSync(path.join(dir, f), "utf8") };
}
const input = {
  language: "Solidity",
  sources,
  settings: {
    optimizer: { enabled: true, runs: 200 },
    viaIR: true,
    evmVersion: "cancun",
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};

const out = JSON.parse(solc.compile(JSON.stringify(input)));
const errors = (out.errors || []).filter((e) => e.severity === "error");
(out.errors || []).forEach((e) => console.error(e.formattedMessage));
if (errors.length) process.exit(1);

fs.mkdirSync(path.join(__dirname, "build"), { recursive: true });
for (const [file, contracts] of Object.entries(out.contracts)) {
  for (const [name, c] of Object.entries(contracts)) {
    fs.writeFileSync(
      path.join(__dirname, "build", `${name}.json`),
      JSON.stringify({ abi: c.abi, bytecode: "0x" + c.evm.bytecode.object }, null, 2)
    );
    console.log(`OK → build/${name}.json`);
  }
}
console.log("solc " + solc.version());
