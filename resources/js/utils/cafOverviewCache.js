const TTL_MS = 5 * 60 * 1000;

const overviewCache = new Map();
let managersCache = null;
let managersCacheAt = 0;

export function overviewCacheKey(cafCode, month, year) {
  return `${String(cafCode || '').trim()}|${month}|${year}`;
}

export function getCachedOverview(cafCode, month, year) {
  return overviewCache.get(overviewCacheKey(cafCode, month, year)) || null;
}

export function setCachedOverview(cafCode, month, year, data) {
  if (!data) return;
  overviewCache.set(overviewCacheKey(cafCode, month, year), {
    data,
    fetchedAt: Date.now(),
  });
}

export function isOverviewCacheFresh(entry, maxAge = TTL_MS) {
  return Boolean(entry?.data) && Date.now() - (entry.fetchedAt || 0) < maxAge;
}

export function getCachedManagers() {
  if (managersCache && Date.now() - managersCacheAt < TTL_MS) {
    return managersCache;
  }
  return null;
}

export function setCachedManagers(list) {
  managersCache = Array.isArray(list) ? list : [];
  managersCacheAt = Date.now();
}
