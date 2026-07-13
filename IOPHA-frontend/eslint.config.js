const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const globals = require("globals");
const queryPlugin = require("@tanstack/eslint-plugin-query");
const securityPlugin = require("eslint-plugin-security");
const sonarjsPlugin = require("eslint-plugin-sonarjs");
const promisePlugin = require("eslint-plugin-promise");
const nPlugin = require("eslint-plugin-n");
const regexpPlugin = require("eslint-plugin-regexp");
const noSecretsPlugin = require("eslint-plugin-no-secrets");

module.exports = [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      "@tanstack/query": queryPlugin,
      security: securityPlugin,
      sonarjs: sonarjsPlugin,
      promise: promisePlugin,
      n: nPlugin,
      regexp: regexpPlugin,
      "no-secrets": noSecretsPlugin,
    },
    rules: {
      "@typescript-eslint/no-unused-vars": "warn",
      "@tanstack/query/exhaustive-deps": "error",
      "security/detect-eval-with-expression": "error",
      "security/detect-non-literal-fs-filename": "warn",
      "security/detect-child-process": "error",
      "security/detect-pseudoRandomBytes": "warn",
      "no-secrets/no-secrets": "error",
      "sonarjs/cognitive-complexity": ["warn", 15],
      "sonarjs/no-duplicate-string": "warn",
      "promise/catch-or-return": "error",
      "promise/no-nesting": "warn",
      "n/no-deprecated-api": "error",
      "n/no-missing-require": "off",
      "regexp/no-super-linear-backtracking": "error",
      "regexp/no-useless-flag": "warn",
    },
  },
  {
    files: ["**/*.ts", "**/*.tsx"],
    rules: {
      "n/no-missing-import": "off",
      "n/no-unsupported-features/es-syntax": "off",
      "n/no-unsupported-features/node-builtins": "off",
    },
  },
  {
    files: [
      "cypress/**/*",
      "**/*.spec.tsx",
      "**/*.spec.ts",
      "**/*.steps.ts",
      "**/*.mock.ts",
      "**/*.mock.tsx",
    ],
    rules: {
      "no-secrets/no-secrets": "off",
      "promise/catch-or-return": "off",
      "sonarjs/no-duplicate-string": "off",
      "@typescript-eslint/no-namespace": "off",
    },
  },
  {
    files: ["**/*.config.ts", "**/*.config.js", "cypress.config.ts"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
  {
    ignores: ["node_modules/", "dist/"],
  },
];
