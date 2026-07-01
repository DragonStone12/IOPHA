#!/usr/bin/env node

/**
 * Checks for duplicate Cucumber step definitions across all step files.
 * Exits with error if duplicates are found.
 */

const fs = require("fs");
const path = require("path");

const STEPS_DIR = path.join(
  __dirname,
  "..",
  "cypress/support/step_definitions",
);
const STEP_PATTERN = /^(Given|When|Then|And)\(\s*["'`](.+?)["'`]/m;

function findStepDefinitions() {
  const files = fs.readdirSync(STEPS_DIR).filter((f) => f.endsWith(".ts"));
  const definitions = new Map();

  for (const file of files) {
    const filePath = path.join(STEPS_DIR, file);
    const content = fs.readFileSync(filePath, "utf-8");
    const lines = content.split("\n");

    for (let i = 0; i < lines.length; i++) {
      const match = lines[i].match(STEP_PATTERN);
      if (match) {
        const [, type, step] = match;
        const key = `${type}:${step}`;

        if (!definitions.has(key)) {
          definitions.set(key, []);
        }
        definitions.get(key).push({ file, line: i + 1 });
      }
    }
  }

  return definitions;
}

function checkDuplicates() {
  const definitions = findStepDefinitions();
  const duplicates = [];

  for (const [key, locations] of definitions) {
    if (locations.length > 1) {
      duplicates.push({ key, locations });
    }
  }

  if (duplicates.length > 0) {
    console.error("❌ Duplicate step definitions found:\n");
    for (const { key, locations } of duplicates) {
      console.error(`  "${key}"`);
      for (const { file, line } of locations) {
        console.error(`    - ${file}:${line}`);
      }
      console.error();
    }
    console.error(
      "Each step definition must be unique across all step files.\n" +
        "Move shared steps to app.steps.ts and keep feature-specific steps in separate files.",
    );
    process.exit(1);
  }

  console.log("✅ No duplicate step definitions found.");
}

checkDuplicates();
