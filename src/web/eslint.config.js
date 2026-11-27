import js from "@eslint/js";
import noUnsanitized from "eslint-plugin-no-unsanitized";
import svelte from "eslint-plugin-svelte";
import ts from "typescript-eslint";

export default ts.config(
  { ignores: ["dist/", "coverage/", "node_modules/"] },
  js.configs.recommended,
  ...ts.configs.strict,
  ...svelte.configs["flat/recommended"],
  noUnsanitized.configs.recommended,
  {
    rules: { "svelte/no-at-html-tags": "error" },
  },
  {
    files: ["**/*.svelte", "**/*.svelte.ts"],
    languageOptions: { parserOptions: { parser: ts.parser } },
  },
);
