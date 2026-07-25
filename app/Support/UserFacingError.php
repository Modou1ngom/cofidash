<?php

namespace App\Support;

/**
 * Messages d'erreur destinés à l'UI — sans détails techniques (JSON, .env, Oracle, stack).
 */
class UserFacingError
{
    public const GENERIC = 'Les données n\'ont pas pu être chargées. Veuillez réessayer dans un moment.';

    public const SERVICE_UNAVAILABLE = 'Le service de données est temporairement indisponible. Veuillez réessayer plus tard.';

    public const TIMEOUT = 'Le chargement a pris trop de temps. Veuillez réessayer.';

    public const CONNECTION = 'Impossible de se connecter au service de données. Veuillez réessayer plus tard.';

    /**
     * Transforme une erreur brute (corps Python, exception, JSON) en message utilisateur.
     */
    public static function from(mixed $raw, ?string $fallback = null): string
    {
        $fallback = $fallback ?: self::GENERIC;
        $text = self::normalize($raw);

        if ($text === '') {
            return $fallback;
        }

        $lower = mb_strtolower($text);

        if (self::looksTechnical($text, $lower)) {
            if (str_contains($lower, 'timeout') || str_contains($lower, 'timed out') || str_contains($lower, 'curl error 28')) {
                return self::TIMEOUT;
            }
            if (
                str_contains($lower, 'connection refused')
                || str_contains($lower, 'failed to connect')
                || str_contains($lower, 'curl error 7')
                || str_contains($lower, 'could not connect')
            ) {
                return self::CONNECTION;
            }
            if (
                str_contains($lower, 'mot de passe')
                || str_contains($lower, 'password')
                || str_contains($lower, 'oracle')
                || str_contains($lower, 'python')
                || str_contains($lower, '.env')
            ) {
                return self::SERVICE_UNAVAILABLE;
            }

            return $fallback;
        }

        // Message déjà court et non technique
        if (mb_strlen($text) > 180) {
            return $fallback;
        }

        return $text;
    }

    private static function normalize(mixed $raw): string
    {
        if ($raw === null) {
            return '';
        }
        if (is_array($raw)) {
            if (isset($raw['detail'])) {
                return self::normalize($raw['detail']);
            }
            if (isset($raw['message'])) {
                return self::normalize($raw['message']);
            }
            $encoded = json_encode($raw, JSON_UNESCAPED_UNICODE);

            return is_string($encoded) ? $encoded : '';
        }
        if (! is_string($raw) && ! is_numeric($raw)) {
            return '';
        }

        $text = trim((string) $raw);
        if ($text === '') {
            return '';
        }

        // Corps JSON FastAPI : {"detail":"..."}
        if (str_starts_with($text, '{') || str_starts_with($text, '[')) {
            $decoded = json_decode($text, true);
            if (json_last_error() === JSON_ERROR_NONE) {
                return self::normalize($decoded);
            }
        }

        // HTML / page d'erreur proxy
        if (str_starts_with($text, '<')) {
            return '';
        }

        return $text;
    }

    private static function looksTechnical(string $text, string $lower): bool
    {
        if (str_starts_with($text, '{') || str_starts_with($text, '[')) {
            return true;
        }
        if (preg_match('/\bORA-\d{5}\b/i', $text)) {
            return true;
        }
        if (preg_match('/\bORACLE_[A-Z0-9_]+\b/', $text)) {
            return true;
        }
        if (preg_match('/\b(PYTHON_SERVICE_URL|APP_KEY|\.env)\b/i', $text)) {
            return true;
        }
        if (preg_match('/\b(curl error|traceback|stack trace|exception|sqlalchemy|fastapi)\b/i', $text)) {
            return true;
        }
        if (preg_match('/\b\d{1,3}(?:\.\d{1,3}){3}:\d+\b/', $text)) {
            return true; // host:port
        }
        if (str_contains($lower, 'fichier .env') || str_contains($lower, 'définissez ')) {
            return true;
        }

        return false;
    }
}
