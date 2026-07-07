#!/usr/bin/env node

const { execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const MONO_ROOT = path.join(__dirname, "..");
const FRONTEND_DIR = path.join(MONO_ROOT, "IOPHA-frontend");

try {
  const changedFiles = execFileSync("git", ["diff", "--name-only", "main...HEAD"], {
    encoding: "utf-8",
    cwd: MONO_ROOT,
  })
    .trim()
    .split("\n")
    .filter((file) => file.length > 0);

  const componentFiles = changedFiles.filter((file) =>
    file.startsWith("IOPHA-frontend/src/components/"),
  );

  const specFiles = changedFiles.filter((file) =>
    file.startsWith("IOPHA-frontend/src/components/"),
  );

  const specsToRun = new Set();

  specFiles.forEach((file) => {
    if (file.endsWith(".spec.tsx") || file.endsWith(".spec.ts")) {
      const relativePath = file.replace("IOPHA-frontend/", "");
      specsToRun.add(relativePath);
    }
  });

  componentFiles.forEach((file) => {
    if (!file.endsWith(".spec.tsx") && !file.endsWith(".spec.ts")) {
      const specFile = file.replace(/\.tsx?$/, ".spec.tsx");
      const relativePath = specFile.replace("IOPHA-frontend/", "");
      const fullPath = path.join(MONO_ROOT, "IOPHA-frontend", relativePath);
      if (fs.existsSync(fullPath)) {
        specsToRun.add(relativePath);
      }
    }
  });

  if (specsToRun.size === 0) {
    console.log("No component tests changed, skipping component tests");
  } else {
    const specList = Array.from(specsToRun).join(",");
    console.log(`Running ${specsToRun.size} changed component test(s):`);
    console.log(specList);

    execFileSync(
      "npx",
      ["cypress", "run", "--component", "--headless", "--spec", specList],
      { cwd: FRONTEND_DIR, stdio: "inherit" },
    );
  }

  console.log("\nRunning E2E tests (headless, mirroring CI)...");
  execFileSync(
    "npx",
    ["start-server-and-test", "dev", "http://localhost:3000", "npx cypress run --e2e --headless"],
    { cwd: FRONTEND_DIR, stdio: "inherit" },
  );
} catch (error) {
  process.exit(1);
}
