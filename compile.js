// Kontratı derler: node compile.js  →  build/AIEscrow.json (abi + bytecode)
// Gerekli: npm install  (package.json içindeki solc paketi)
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const src = fs.readFileSync(path.join(__dirname, "contracts", "AIEscrow.sol"), "utf8");
const input = {
  language: "Solidity",
  sources: { "AIEscrow.sol": { content: src } },
  settings: {
    optimizer: { enabled: true, runs: 200 },
    evmVersion: "cancun",
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};

const out = JSON.parse(solc.compile(JSON.stringify(input)));
const errors = (out.errors || []).filter((e) => e.severity === "error");
(out.errors || []).forEach((e) => console.error(e.formattedMessage));
if (errors.length) process.exit(1);

const c = out.contracts["AIEscrow.sol"].AIEscrow;
fs.mkdirSync(path.join(__dirname, "build"), { recursive: true });
fs.writeFileSync(
  path.join(__dirname, "build", "AIEscrow.json"),
  JSON.stringify({ abi: c.abi, bytecode: "0x" + c.evm.bytecode.object }, null, 2)
);
console.log("OK → build/AIEscrow.json (solc " + solc.version() + ")");
