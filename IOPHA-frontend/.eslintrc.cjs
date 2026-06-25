module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint", "@tanstack/query"],
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  env: {
    browser: true,
    es2020: true,
  },
  rules: {
    "@typescript-eslint/no-unused-vars": "warn",
    "@tanstack/query/exhaustive-deps": "error",
  },
};
