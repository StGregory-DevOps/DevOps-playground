import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        setTimeout: "readonly",
        fetch: "readonly",
        AbortSignal: "readonly",
      },
    },
    rules: {
      eqeqeq: "error",
      curly: "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
];
