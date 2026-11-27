// ESLint configuration for TREE OS JavaScript (CLAUDE.md sections 5.4, 13).
// GJS shell-extension code will need its own globals when it is added.
import js from "@eslint/js";

export default [
  {
    ignores: [".venv/", "node_modules/", "build/", "output/"],
  },
  js.configs.recommended,
  {
    files: ["**/*.js", "**/*.mjs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
  },
  {
    // GNOME Shell extension code runs in GJS, which provides console.* globals
    // and gi:// / resource:// module specifiers. No Node globals are assumed.
    files: ["desktop/**/*.js"],
    languageOptions: {
      globals: {
        console: "readonly",
        // GNOME Shell provides `global` (for example global.backend) to extensions.
        global: "readonly",
      },
    },
  },
];
