import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import process from "node:process";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ALLOWED_LICENSES,
  findOffenders,
  isAllowed,
  main,
  readInstalledLicense,
} from "./check-licenses.mjs";

describe("isAllowed", () => {
  it.each(["MIT", "MIT-0", "ISC", "Apache-2.0", "MPL-2.0", "CC-BY-4.0", "0BSD", "BlueOak-1.0.0"])(
    "allows %s",
    (license) => {
      expect(isAllowed(license)).toBe(true);
    },
  );

  it.each([
    "GPL-3.0-only",
    "AGPL-3.0",
    "Unlicense",
    "Python-2.0",
    "UNKNOWN",
    "UNLICENSED",
    "",
    "   ",
  ])("rejects %s", (license) => {
    expect(isAllowed(license)).toBe(false);
  });

  it("rejects a missing or non-string license", () => {
    expect(isAllowed(undefined)).toBe(false);
    expect(isAllowed(null)).toBe(false);
    expect(isAllowed({ type: "MIT" })).toBe(false);
  });

  it("passes OR when any side is allowed", () => {
    expect(isAllowed("GPL-3.0-only OR MIT")).toBe(true);
    expect(isAllowed("MIT OR GPL-3.0-only")).toBe(true);
    expect(isAllowed("GPL-3.0-only OR AGPL-3.0")).toBe(false);
  });

  it("needs every side of AND", () => {
    expect(isAllowed("MIT AND ISC")).toBe(true);
    expect(isAllowed("MIT AND GPL-3.0-only")).toBe(false);
  });

  it("binds AND tighter than OR", () => {
    expect(isAllowed("GPL-3.0-only AND MIT OR ISC")).toBe(true);
    expect(isAllowed("GPL-3.0-only AND MIT OR AGPL-3.0")).toBe(false);
  });

  it("handles parentheses", () => {
    expect(isAllowed("(MIT OR GPL-3.0-only) AND ISC")).toBe(true);
    expect(isAllowed("(GPL-3.0-only OR AGPL-3.0) AND MIT")).toBe(false);
    expect(isAllowed("MIT AND (GPL-3.0-only OR ISC)")).toBe(true);
    expect(isAllowed("(MIT)")).toBe(true);
  });

  it("rejects a malformed expression", () => {
    for (const bad of ["(MIT", "MIT)", "MIT OR", "AND MIT", "MIT ISC", "()"]) {
      expect(isAllowed(bad)).toBe(false);
    }
  });

  it("uses a custom allowlist", () => {
    expect(isAllowed("GPL-3.0-only", new Set(["GPL-3.0-only"]))).toBe(true);
    expect(ALLOWED_LICENSES.has("GPL-3.0-only")).toBe(false);
  });
});

describe("findOffenders", () => {
  it("returns nothing when every package is allowed and skips the root entry", () => {
    const lock = {
      packages: {
        "": { license: "GPL-3.0-only" },
        "node_modules/a": { version: "1.0.0", license: "MIT" },
        "node_modules/b": { version: "2.0.0", license: "(MIT OR GPL-3.0-only)" },
      },
    };
    expect(findOffenders(lock)).toEqual([]);
  });

  it("names each offender with path, version and license", () => {
    const lock = {
      packages: {
        "node_modules/ok": { version: "1.0.0", license: "MIT-0" },
        "node_modules/bad": { version: "2.0.0", license: "GPL-3.0-only" },
        "node_modules/gone": { version: "3.0.0" },
        "node_modules/unk": { version: "4.0.0", license: "UNKNOWN" },
        "node_modules/nover": { license: "AGPL-3.0" },
      },
    };
    expect(findOffenders(lock)).toEqual([
      { path: "node_modules/bad", version: "2.0.0", license: "GPL-3.0-only" },
      { path: "node_modules/gone", version: "3.0.0", license: "MISSING" },
      { path: "node_modules/unk", version: "4.0.0", license: "UNKNOWN" },
      { path: "node_modules/nover", version: "unknown", license: "AGPL-3.0" },
    ]);
  });

  it("handles a lockfile without packages", () => {
    expect(findOffenders({})).toEqual([]);
  });
});

describe("with files on disk", () => {
  let root = "";

  beforeEach(() => {
    root = mkdtempSync(path.join(tmpdir(), "check-licenses-"));
  });

  afterEach(() => {
    rmSync(root, { recursive: true, force: true });
    vi.restoreAllMocks();
  });

  const install = (name, manifest) => {
    mkdirSync(path.join(root, "node_modules", name), { recursive: true });
    writeFileSync(path.join(root, "node_modules", name, "package.json"), JSON.stringify(manifest));
  };

  const writeLock = (packages) => {
    writeFileSync(path.join(root, "package-lock.json"), JSON.stringify({ packages }));
  };

  it("reads an installed license, or nothing", () => {
    install("a", { license: "MIT" });
    install("b", { license: { type: "MIT" } });
    expect(readInstalledLicense(root, "node_modules/a")).toBe("MIT");
    expect(readInstalledLicense(root, "node_modules/b")).toBeUndefined();
    expect(readInstalledLicense(root, "node_modules/none")).toBeUndefined();
  });

  it("falls back to the installed package.json when the lockfile has no license", () => {
    install("a", { license: "MIT" });
    install("b", { license: "GPL-3.0-only" });
    const lock = {
      packages: {
        "node_modules/a": { version: "1.0.0" },
        "node_modules/b": { version: "1.0.0" },
        "node_modules/c": { version: "1.0.0" },
      },
    };
    expect(findOffenders(lock, { root }).map((o) => [o.path, o.license])).toEqual([
      ["node_modules/b", "GPL-3.0-only"],
      ["node_modules/c", "MISSING"],
    ]);
  });

  it("main returns 0 and reports the count when all licenses are allowed", () => {
    writeLock({ "": {}, "node_modules/a": { version: "1.0.0", license: "MIT" } });
    const out = vi.spyOn(process.stdout, "write").mockReturnValue(true);
    expect(main(root)).toBe(0);
    expect(out).toHaveBeenCalledWith("All 1 packages have an allowed license.\n");
  });

  it("main returns 1 and names each offender when a license is disallowed", () => {
    writeLock({
      "": {},
      "node_modules/a": { version: "1.0.0", license: "MIT" },
      "node_modules/bad": { version: "2.0.0", license: "GPL-3.0-only" },
    });
    const err = vi.spyOn(process.stderr, "write").mockReturnValue(true);
    expect(main(root)).toBe(1);
    expect(err).toHaveBeenCalledWith("Disallowed license: node_modules/bad 2.0.0 (GPL-3.0-only)\n");
  });
});
