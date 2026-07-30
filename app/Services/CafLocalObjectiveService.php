<?php

namespace App\Services;

use App\Models\Objective;
use App\Models\User;
use Illuminate\Support\Collection;

/**
 * Objectifs CAF fixés par le Chef d'Agence (CA) — stockés en local (MySQL `objectives`), pas DASH.
 */
class CafLocalObjectiveService
{
    /**
     * @return array{loan_count_objective: float, monthly_volume_objective: float}
     */
    public function productionObjectivesForUser(User $user, int $month, int $year): array
    {
        $empty = [
            'loan_count_objective' => 0.0,
            'monthly_volume_objective' => 0.0,
        ];

        $objectives = $this->candidatesByType('PRODUCTION', $month, $year);
        if ($objectives->isEmpty()) {
            return $empty;
        }

        $matched = $this->matchObjectiveForCaf($user, $objectives);
        if ($matched === null) {
            return $empty;
        }

        return [
            'loan_count_objective' => (float) ($matched->value_nombres ?? $matched->value ?? 0),
            'monthly_volume_objective' => (float) ($matched->value_volume ?? 0),
        ];
    }

    /**
     * Objectif New Deal (nombre de dossiers) fixé par le CA pour un CAF.
     *
     * @return array{loan_count_objective: float}
     */
    public function newDealObjectivesForUser(User $user, int $month, int $year): array
    {
        $empty = ['loan_count_objective' => 0.0];

        $objectives = $this->candidatesByType('NEW_DEAL', $month, $year);
        if ($objectives->isEmpty()) {
            return $empty;
        }

        $matched = $this->matchObjectiveForCaf($user, $objectives);
        if ($matched === null) {
            return $empty;
        }

        return [
            'loan_count_objective' => (float) ($matched->value_nombres ?? $matched->value ?? 0),
        ];
    }

    /**
     * @return Collection<int, Objective>
     */
    private function candidatesByType(string $type, int $month, int $year): Collection
    {
        $quarter = (int) ceil($month / 3);

        return Objective::query()
            ->where('type', $type)
            ->where('year', $year)
            ->where(function ($q) use ($month, $quarter) {
                $q->where(function ($q2) use ($month) {
                    $q2->where('period', 'month')->where('month', $month);
                })->orWhere(function ($q2) use ($quarter) {
                    $q2->where('period', 'quarter')->where('quarter', $quarter);
                })->orWhere('period', 'year');
            })
            ->whereIn('status', ['validated', 'pending_validation'])
            ->orderByRaw("CASE WHEN status = 'validated' THEN 0 ELSE 1 END")
            ->orderByRaw("CASE period WHEN 'month' THEN 0 WHEN 'quarter' THEN 1 ELSE 2 END")
            ->orderByDesc('updated_at')
            ->get();
    }

    /**
     * @param  Collection<int, Objective>  $objectives
     */
    private function matchObjectiveForCaf(User $user, Collection $objectives): ?Objective
    {
        $user->loadMissing('agency');

        $name = trim((string) $user->name);
        if ($name !== '') {
            $needle = 'CAF: '.$name;
            $byName = $objectives->first(
                fn (Objective $obj) => stripos((string) $obj->agency_name, $needle) !== false
            );
            if ($byName !== null) {
                return $byName;
            }
        }

        $identifiers = array_values(array_filter([
            (string) $user->id,
            trim((string) $user->email),
            trim((string) ($user->manager_code ?? '')),
        ], fn (string $v) => $v !== ''));

        if ($identifiers !== []) {
            $byCode = $objectives->first(
                fn (Objective $obj) => in_array((string) $obj->agency_code, $identifiers, true)
            );
            if ($byCode !== null) {
                return $byCode;
            }
        }

        if ($user->agency) {
            $agencyCodes = array_values(array_filter([
                trim((string) $user->agency->code),
                (string) $user->agency->id,
                trim((string) ($user->agency->name ?? '')),
            ], fn (string $v) => $v !== ''));

            return $objectives->first(
                fn (Objective $obj) => in_array((string) $obj->agency_code, $agencyCodes, true)
            );
        }

        return null;
    }
}
