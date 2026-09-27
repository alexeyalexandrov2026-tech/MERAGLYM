import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Vendored third-party OSINT tool sources kept for reference only.
    // These are not part of the application and must not be linted.
    "staging_archives/**",
    "python/**",
    // Generated Prisma clients and desktop build outputs.
    "src/generated/**",
    "dist-electron/**",
    "release/**",
  ]),
]);

export default eslintConfig;
