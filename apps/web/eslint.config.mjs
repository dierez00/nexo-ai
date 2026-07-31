import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

// eslint-config-next 16 exporta flat config directamente; el FlatCompat de eslintrc
// revienta con "Converting circular structure to JSON" al normalizarlo.
const eslintConfig = [
  { ignores: [".next", "out", "build", "next-env.d.ts", "src/generated/**"] },
  ...nextCoreWebVitals,
  ...nextTypescript,
];

export default eslintConfig;
