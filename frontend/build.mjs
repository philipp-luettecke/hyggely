// Bundle the heating panel into the one module the integration serves.
//
//   node build.mjs                 writes the module into the integration
//   node build.mjs --outfile=PATH  writes it elsewhere, e.g. to compare with it
//
// Not minified: the checked-in module stays readable in reviews, and changes of
// different sections land in different places of it.
import * as esbuild from "esbuild";

const MODULE = "../custom_components/climate_control/frontend/heating-panel.js";

const outfileArgument = process.argv.find((argument) =>
  argument.startsWith("--outfile="),
);

await esbuild.build({
  entryPoints: ["src/heating-panel.ts"],
  outfile: outfileArgument ? outfileArgument.slice("--outfile=".length) : MODULE,
  bundle: true,
  format: "esm",
  target: ["es2021", "safari15"],
  charset: "utf8",
  legalComments: "eof",
  logLevel: "warning",
});
