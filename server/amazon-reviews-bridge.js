/**
 * Bridge: amazon-reviews-skill JSON → amz-competitor-analysis /api/local/reviews shape.
 * Keep response compatible with LocalProvider._loadExternalReviews / normalizeReviewRows.
 */
const fs = require("fs");
const path = require("path");

function resolveSkillDataDirs(scanRoot, root) {
  const candidates = [
    /* Prefer skill embedded inside this repo */
    path.resolve(root, "amazon-reviews-skill", "data"),
    path.resolve(scanRoot, "amazon-reviews-skill", "data"),
    path.resolve(root, "..", "amazon-reviews-skill", "data"),
    path.resolve(scanRoot, "..", "amazon-reviews-skill", "data"),
    path.resolve(root, "..", "..", "amazon-reviews-skill", "data"),
  ];
  const seen = new Set();
  const out = [];
  for (const dir of candidates) {
    const key = path.normalize(dir).toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    if (fs.existsSync(dir)) out.push(dir);
  }
  return out;
}

function siteToSkillCode(site) {
  const map = {
    US: "com",
    UK: "co.uk",
    GB: "co.uk",
    DE: "de",
    FR: "fr",
    IT: "it",
    ES: "es",
    JP: "co.jp",
    CA: "ca",
    AU: "com.au",
    MX: "com.mx",
    IN: "in",
  };
  const raw = String(site || "US").trim();
  return (map[raw.toUpperCase()] || raw.toLowerCase().replace(/^\./, "") || "com").toLowerCase();
}

function reviewKey(row) {
  const id = String(row.review_id || row.reviewId || "").trim().toUpperCase();
  if (id) return "id:" + id;
  const blob = [row.asin, row.date, row.author || row.reviewerName, row.title, row.content]
    .map((x) => String(x || "").trim().toLowerCase())
    .join("|");
  return "sig:" + blob.slice(0, 240);
}

function mapSkillReview(item, asin, sourceFile) {
  const body = item.body || item.content || item.text || item.comment || "";
  const title = item.title || item.reviewTitle || "";
  const author = item.author || item.reviewerName || item.reviewer || "";
  return {
    asin: String(item.asin || asin || "").trim().toUpperCase(),
    title: title || null,
    content: body || null,
    body: body || null,
    text: [title, body].filter(Boolean).join("：") || null,
    rating: item.rating != null ? item.rating : item.star != null ? item.star : null,
    date: item.date_text || item.date || item.reviewDate || null,
    date_text: item.date_text || item.date || null,
    review_id: item.review_id || item.reviewId || item.id || null,
    reviewId: item.review_id || item.reviewId || item.id || null,
    author: author || null,
    reviewerName: author || null,
    verified: item.verified,
    helpful_votes: item.helpful_votes,
    source_url: item.source_url || null,
    sourceFile: sourceFile,
    source: "amazon-reviews-skill",
  };
}

/**
 * Load crawl outputs: data/reviews_{ASIN}_{site}.json
 * @returns {{ reviews: object[], matchedFiles: string[], searchedFiles: number, source: string, count: number, unique_review_ids: number } | null}
 */
function loadSkillReviews({ scanRoot, root, asin, site, limit }) {
  const needle = String(asin || "").trim().toUpperCase();
  if (!/^[A-Z0-9]{10}$/.test(needle)) return null;
  const expectedSite = siteToSkillCode(site || "US");

  const dirs = resolveSkillDataDirs(scanRoot, root);
  if (!dirs.length) return null;

  const matchedFiles = [];
  const reviews = [];
  let searchedFiles = 0;
  let metaCount = 0;
  let metaUnique = 0;

  for (const dir of dirs) {
    let names = [];
    try {
      names = fs.readdirSync(dir);
    } catch (err) {
      continue;
    }
    for (const name of names) {
      if (!/^reviews_/i.test(name) || !name.toLowerCase().endsWith(".json")) continue;
      searchedFiles += 1;
      if (!name.toUpperCase().includes(needle)) continue;
      const fileSiteMatch = name.match(/^reviews_[A-Z0-9]{10}_(.+)\.json$/i);
      const fileSite = fileSiteMatch && fileSiteMatch[1] ? fileSiteMatch[1].toLowerCase() : "";
      if (expectedSite && fileSite && fileSite !== expectedSite) continue;
      const fp = path.join(dir, name);
      let data;
      try {
        data = JSON.parse(fs.readFileSync(fp, "utf8"));
      } catch (err) {
        continue;
      }
      const fileAsin = String((data && data.asin) || "").trim().toUpperCase();
      if (fileAsin && fileAsin !== needle) continue;
      const rows = Array.isArray(data && data.reviews) ? data.reviews : [];
      if (!rows.length) continue;
      matchedFiles.push(fp);
      metaCount = Number(data.count) || rows.length;
      metaUnique = Number(data.unique_review_ids) || rows.length;
      for (const row of rows) {
        const mapped = mapSkillReview(row, needle, fp);
        if (!mapped.content && !mapped.title) continue;
        if (mapped.asin && mapped.asin !== needle) continue;
        reviews.push(mapped);
      }
    }
  }

  if (!reviews.length) return null;

  const dedup = [];
  const seen = new Set();
  for (const row of reviews) {
    const key = reviewKey(row);
    if (seen.has(key)) continue;
    seen.add(key);
    dedup.push(row);
  }

  let out = dedup;
  if (limit && limit > 0) out = out.slice(0, limit);

  return {
    reviews: out,
    matchedFiles,
    searchedFiles,
    source: "amazon-reviews-skill",
    count: metaCount || out.length,
    unique_review_ids: metaUnique || out.length,
    rawCount: reviews.length,
    duplicateCount: Math.max(0, reviews.length - dedup.length),
  };
}

function mergeReviewsPreferSkill(skillPayload, localPayload, limit) {
  const local = localPayload && typeof localPayload === "object" ? localPayload : { reviews: [] };
  const localReviews = Array.isArray(local.reviews) ? local.reviews : [];
  const skillReviews = skillPayload && Array.isArray(skillPayload.reviews) ? skillPayload.reviews : [];

  if (!skillReviews.length) {
    return local;
  }

  const merged = [];
  const seen = new Set();
  for (const row of skillReviews.concat(localReviews)) {
    const key = reviewKey(row);
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(row);
  }
  let reviews = merged;
  if (limit && limit > 0) reviews = reviews.slice(0, limit);

  const matchedFiles = []
    .concat(skillPayload.matchedFiles || [])
    .concat(local.matchedFiles || []);

  return Object.assign({}, local, {
    reviews,
    matchedFiles,
    searchedFiles: Number(local.searchedFiles || 0) + Number(skillPayload.searchedFiles || 0),
    rawCount: Number(local.rawCount || localReviews.length) + Number(skillPayload.rawCount || skillReviews.length),
    duplicateCount: Math.max(0, Number(local.duplicateCount || 0) + Number(skillPayload.duplicateCount || 0)),
    source: skillPayload.source,
    skill: {
      count: skillPayload.count,
      unique_review_ids: skillPayload.unique_review_ids,
      matchedFiles: skillPayload.matchedFiles,
    },
  });
}

function siteCodeFromReviewFile(value, asin) {
  const text = String(value || "").replace(/\\/g, "/");
  const needle = String(asin || "").trim().toUpperCase();
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp("reviews_" + escaped + "_([^/]+)\\.json$", "i");
  const m = text.match(re);
  return m && m[1] ? m[1].toLowerCase() : "";
}

function filterLocalPayloadBySite(localPayload, asin, site) {
  const local = localPayload && typeof localPayload === "object" ? Object.assign({}, localPayload) : { reviews: [] };
  const expectedSite = siteToSkillCode(site || "US");
  const keepFile = (file) => {
    const fileSite = siteCodeFromReviewFile(file, asin);
    return !fileSite || fileSite === expectedSite;
  };
  if (Array.isArray(local.reviews)) {
    local.reviews = local.reviews.filter((row) => {
      const fileSite = siteCodeFromReviewFile(row && (row.sourceFile || row.file || row.path), asin);
      return !fileSite || fileSite === expectedSite;
    });
  }
  if (Array.isArray(local.rows)) {
    local.rows = local.rows.filter((row) => {
      const fileSite = siteCodeFromReviewFile(row && (row.sourceFile || row.file || row.path), asin);
      return !fileSite || fileSite === expectedSite;
    });
  }
  if (Array.isArray(local.matchedFiles)) {
    local.matchedFiles = local.matchedFiles.filter(keepFile);
  }
  const reviewCount = Array.isArray(local.reviews) ? local.reviews.length : (Array.isArray(local.rows) ? local.rows.length : 0);
  local.rawCount = reviewCount;
  local.duplicateCount = Math.max(0, Number(local.duplicateCount) || 0);
  return local;
}

function buildLocalReviewsResponse({ scanRoot, root, asin, site, fileOverride, limit, getLocalData }) {
  const skill = loadSkillReviews({ scanRoot, root, asin, site, limit: 0 });
  // Prefer skill dump; skip directory scan merge to avoid double-counting the same JSON
  // (scan path often lacks review_id so dedupe by signature fails).
  if (skill && Array.isArray(skill.reviews) && skill.reviews.length) {
    let reviews = skill.reviews;
    if (limit && limit > 0) reviews = reviews.slice(0, limit);
    return {
      reviews,
      matchedFiles: skill.matchedFiles || [],
      searchedFiles: skill.searchedFiles || 0,
      rawCount: skill.rawCount || reviews.length,
      duplicateCount: skill.duplicateCount || 0,
      source: skill.source,
      skill: {
        count: skill.count,
        unique_review_ids: skill.unique_review_ids,
        matchedFiles: skill.matchedFiles,
      },
    };
  }
  const local = typeof getLocalData === "function"
    ? getLocalData("reviews", asin, fileOverride, limit)
    : { reviews: [] };
  return mergeReviewsPreferSkill(null, filterLocalPayloadBySite(local, asin, site), limit);
}

module.exports = {
  loadSkillReviews,
  mergeReviewsPreferSkill,
  buildLocalReviewsResponse,
  resolveSkillDataDirs,
  siteToSkillCode,
  filterLocalPayloadBySite,
  mapSkillReview,
};
