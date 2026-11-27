// Checks every package in package-lock.json against a license allowlist.
// Dependency-free on purpose: a license checker must not pull in packages of its own.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

export const ALLOWED_LICENSES = new Set([
  "MIT",
  "MIT-0",
  "ISC",
  "Apache-2.0",
  "BSD-2-Clause",
  "BSD-3-Clause",
  "MPL-2.0",
  "CC-BY-3.0",
  "CC-BY-4.0",
  "0BSD",
  "BlueOak-1.0.0",
  "CC0-1.0",
  "Python-2.0",
  "Unlicense",
]);

/**
 * Whether an SPDX expression is allowed: OR passes if any side is, AND needs every side.
 * AND binds tighter than OR. A missing, unknown or malformed expression is not allowed.
 * @param {unknown} expression
 * @param {ReadonlySet<string>} [allowed]
 * @returns {boolean}
 */
export function isAllowed(expression, allowed = ALLOWED_LICENSES) {
  if (typeof expression !== "string") return false;
  const tokens = expression.match(/\(|\)|[^\s()]+/g) ?? [];
  let pos = 0;

  const parseOr = () => {
    let result = parseAnd();
    while (tokens[pos] === "OR") {
      pos += 1;
      const right = parseAnd();
      result = result || right;
    }
    return result;
  };
  const parseAnd = () => {
    let result = parseAtom();
    while (tokens[pos] === "AND") {
      pos += 1;
      const right = parseAtom();
      result = result && right;
    }
    return result;
  };
  const parseAtom = () => {
    const token = tokens[pos];
    pos += 1;
    if (token === undefined) throw new SyntaxError("unexpected end of expression");
    if (token === "(") {
      const inner = parseOr();
      if (tokens[pos] !== ")") throw new SyntaxError("missing closing parenthesis");
      pos += 1;
      return inner;
    }
    if (token === ")" || token === "AND" || token === "OR") {
      throw new SyntaxError(`unexpected ${token}`);
    }
    return allowed.has(token);
  };

  try {
    const result = parseOr();
    return pos === tokens.length && result;
  } catch {
    return false;
  }
}

/**
 * Read a license from an installed package.json, for lockfile entries without one.
 * @param {string} root
 * @param {string} packagePath
 * @returns {string | undefined}
 */
export function readInstalledLicense(root, packagePath) {
  const file = path.join(root, packagePath, "package.json");
  if (!existsSync(file)) return undefined;
  const license = JSON.parse(readFileSync(file, "utf8")).license;
  return typeof license === "string" ? license : undefined;
}

/**
 * Return one offender per lockfile package whose license is not allowed.
 * @param {{ packages?: Record<string, { version?: string, license?: string }> }} lock
 * @param {{ allowed?: ReadonlySet<string>, root?: string }} [options]
 * @returns {{ path: string, version: string, license: string }[]}
 */
export function findOffenders(lock, options = {}) {
  const { allowed = ALLOWED_LICENSES, root } = options;
  const offenders = [];
  for (const [packagePath, entry] of Object.entries(lock.packages ?? {})) {
    if (packagePath === "") continue;
    let license = entry.license;
    if (license === undefined && root !== undefined) {
      license = readInstalledLicense(root, packagePath);
    }
    if (!isAllowed(license, allowed)) {
      offenders.push({
        path: packagePath,
        version: entry.version ?? "unknown",
        license: license ?? "MISSING",
      });
    }
  }
  return offenders;
}

/**
 * Check the lockfile in a package directory. Returns the process exit code.
 * @param {string} [root]
 * @returns {number}
 */
export function main(root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")) {
  const lock = JSON.parse(readFileSync(path.join(root, "package-lock.json"), "utf8"));
  const offenders = findOffenders(lock, { root });
  const total = Object.keys(lock.packages ?? {}).length - 1;
  if (offenders.length > 0) {
    for (const o of offenders) {
      process.stderr.write(`Disallowed license: ${o.path} ${o.version} (${o.license})\n`);
    }
    process.stderr.write(
      `${offenders.length} of ${total} packages have a license not on the allowlist.\n`,
    );
    return 1;
  }
  process.stdout.write(`All ${total} packages have an allowed license.\n`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main();
}
