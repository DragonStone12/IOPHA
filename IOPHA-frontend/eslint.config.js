const js = require("@eslint/js");
const tseslint = require("typescript-eslint");
const globals = require("globals");
const queryPlugin = require("@tanstack/eslint-plugin-query");

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
    },
    rules: {
      "@typescript-eslint/no-unused-vars": "warn",
      "@tanstack/query/exhaustive-deps": "error",
    },
  },
  {
    ignores: ["node_modules/", "dist/", "cypress/"],
  },
];
