import { test } from "node:test";
import assert from "node:assert/strict";
import { rankNodes, stem, toSearchTerms } from "../src/lib/search";

const node = (name: string, description: string | null = null) => ({ name, description });

// A slice of the real OSINT tree around dating apps, plus look-alikes.
const NODES = [
  node("Dating"),
  node("Tinder (R)", "Dating app. Search public profiles by name and location."),
  node("Bumble (R)", "Dating app; profiles can be looked up by phone number."),
  node("Hinge", "Dating app profile lookup."),
  node("Badoo", "Social discovery and dating site."),
  node("Farmers Only", "Niche dating website."),
  node("Sorted by Birth Date", "People search sorted by date of birth."),
  node("Twitter Date Search", "Search tweets within a date range."),
  node("App Store Search", "Search mobile apps."),
];

const names = (q: string) => rankNodes(NODES, q, toSearchTerms(q)).map((n) => n.name);

test("stem reduces common plurals", () => {
  assert.equal(stem("apps"), "app");
  assert.equal(stem("sites"), "site");
  assert.equal(stem("searches"), "search");
  assert.equal(stem("companies"), "company");
  assert.equal(stem("address"), "address");
  assert.equal(stem("status"), "status");
  assert.equal(stem("dating"), "dating");
});

test("toSearchTerms lowercases, drops stopwords, stems and de-duplicates", () => {
  assert.deepEqual(toSearchTerms("Find the Dating Apps!"), ["find", "dating", "app"]);
  assert.deepEqual(toSearchTerms("app APPS"), ["app"]);
  assert.deepEqual(toSearchTerms("  "), []);
  assert.deepEqual(toSearchTerms("a of"), []);
});

test("'dating' ranks the Dating category first and excludes date-only noise", () => {
  const result = names("dating");
  assert.equal(result[0], "Dating");
  assert.ok(result.includes("Tinder (R)"));
  assert.ok(!result.includes("Sorted by Birth Date"));
  assert.ok(!result.includes("Twitter Date Search"));
});

test("'dating apps' matches entries described as 'dating app'", () => {
  assert.deepEqual(names("dating apps").sort(), ["Bumble (R)", "Hinge", "Tinder (R)"].sort());
});

test("'dating sites' prefers nodes containing both words", () => {
  const result = names("dating sites");
  assert.deepEqual(result.sort(), ["Badoo", "Farmers Only"].sort());
});

test("partial matches are returned instead of nothing", () => {
  // No node contains both words, so the best partial matches come back,
  // with name matches ("Dating") ahead of description-only matches.
  const result = names("dating scam");
  assert.ok(result.length > 0);
  assert.equal(result[0], "Dating");
});

test("fallback ranks the distinctive term above a common one", () => {
  // Mirrors the real tree: no node contains both "dating" and "site", and
  // "site" appears in far more node names than "dating" does.
  const tree = [
    node("Dating"),
    node("Tinder (R)", "Dating app profile search."),
    node("Siteliner", "Find duplicate content on a site."),
    node("SiteSleuth", "Website technology profiler."),
    node("Sitedossier", "Site ownership history."),
    node("Paste Sites"),
    node("Sitediff (T)", "Compare website snapshots."),
    node("Site Explorer"),
    node("Similar Sites"),
    node("Site Checker"),
  ];
  const result = rankNodes(tree, "dating sites", toSearchTerms("dating sites")).map((n) => n.name);
  assert.deepEqual(result.slice(0, 2), ["Dating", "Tinder (R)"]);
  assert.equal(result.length, tree.length);
});

test("a query matching nothing returns an empty list", () => {
  assert.deepEqual(names("zzzqqq"), []);
});
