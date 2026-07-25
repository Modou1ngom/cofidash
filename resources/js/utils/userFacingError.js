/**
 * Messages d'erreur pour l'UI — sans JSON, variables .env, ni détails Oracle.
 */
export function userFacingError(error, fallback = 'Les données n\'ont pas pu être chargées. Veuillez réessayer.') {
  const raw = extractRaw(error);
  if (!raw) return fallback;

  const lower = raw.toLowerCase();

  if (isTechnical(raw, lower)) {
    if (lower.includes('timeout') || lower.includes('timed out') || lower.includes('econnaborted')) {
      return 'Le chargement a pris trop de temps. Veuillez réessayer.';
    }
    if (
      lower.includes('network')
      || lower.includes('connection refused')
      || lower.includes('failed to fetch')
      || lower.includes('err_connection')
    ) {
      return 'Impossible de se connecter au service. Veuillez réessayer plus tard.';
    }
    return 'Le service de données est temporairement indisponible. Veuillez réessayer plus tard.';
  }

  if (raw.length > 180) return fallback;
  return raw;
}

function extractRaw(error) {
  if (error == null) return '';
  if (typeof error === 'string') return unwrapJson(error.trim());

  const data = error?.response?.data;
  if (data) {
    if (typeof data === 'string') return unwrapJson(data.trim());
    const candidate = data.message || data.error || data.detail || '';
    if (typeof candidate === 'string') return unwrapJson(candidate.trim());
    if (candidate && typeof candidate === 'object') {
      return unwrapJson(JSON.stringify(candidate));
    }
  }

  if (typeof error?.message === 'string') return unwrapJson(error.message.trim());
  return '';
}

function unwrapJson(text) {
  if (!text) return '';
  if (text.startsWith('{') || text.startsWith('[')) {
    try {
      const parsed = JSON.parse(text);
      if (parsed?.detail) return unwrapJson(String(parsed.detail));
      if (parsed?.message) return unwrapJson(String(parsed.message));
    } catch {
      return text;
    }
  }
  // "Erreur du service Python. {"detail":"..."}"
  const jsonMatch = text.match(/\{[\s\S]*"detail"[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed?.detail) return String(parsed.detail);
    } catch {
      /* ignore */
    }
  }
  return text;
}

function isTechnical(text, lower) {
  if (text.startsWith('{') || text.startsWith('[') || text.startsWith('<')) return true;
  if (/\bORA-\d{5}\b/i.test(text)) return true;
  if (/\bORACLE_[A-Z0-9_]+\b/.test(text)) return true;
  if (/\b(PYTHON_SERVICE_URL|\.env|traceback|curl error|sqlalchemy|fastapi)\b/i.test(text)) return true;
  if (lower.includes('fichier .env') || lower.includes('définissez ')) return true;
  if (lower.includes('mot de passe oracle') || lower.includes('password')) return true;
  if (/\b\d{1,3}(?:\.\d{1,3}){3}:\d+\b/.test(text)) return true;
  return false;
}
