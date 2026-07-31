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
     * Liste des objectifs CAF (tous types) pour la période.
     * Matching strict : "CAF: {nom}" ou agency_code ∈ {id, email, manager_code}.
     *
     * @return list<array<string, mixed>>
     */
    public function listForUser(User $user, int $month, int $year): array
    {
        $user->loadMissing('agency');
        $quarter = (int) ceil($month / 3);
        $name = trim((string) $user->name);
        $identifiers = array_values(array_filter([
            (string) $user->id,
            trim((string) $user->email),
            trim((string) ($user->manager_code ?? '')),
        ], fn (string $v) => $v !== ''));

        if ($name === '' && $identifiers === []) {
            return [];
        }

        $query = Objective::query()
            ->where('year', $year)
            ->where(function ($q) use ($month, $quarter) {
                $q->where(function ($q2) use ($month) {
                    $q2->where('period', 'month')->where('month', $month);
                })->orWhere(function ($q2) use ($quarter) {
                    $q2->where('period', 'quarter')->where('quarter', $quarter);
                })->orWhere('period', 'year');
            })
            ->whereIn('status', ['validated', 'pending_validation'])
            ->where(function ($q) use ($name, $identifiers) {
                if ($name !== '') {
                    $q->where('agency_name', 'like', '%CAF: '.$name.'%');
                }
                if ($identifiers !== []) {
                    $method = $name !== '' ? 'orWhereIn' : 'whereIn';
                    $q->{$method}('agency_code', $identifiers);
                }
            })
            ->orderBy('type')
            ->orderByRaw("CASE WHEN status = 'validated' THEN 0 ELSE 1 END")
            ->orderByRaw("CASE period WHEN 'month' THEN 0 WHEN 'quarter' THEN 1 ELSE 2 END")
            ->orderByDesc('updated_at')
            ->get();

        // Un seul objectif par type (le plus pertinent déjà trié)
        $byType = [];
        foreach ($query as $obj) {
            $type = (string) $obj->type;
            if (isset($byType[$type])) {
                continue;
            }
            $byType[$type] = [
                'id' => $obj->id,
                'type' => $type,
                'value' => (float) ($obj->value ?? 0),
                'value_nombres' => $obj->value_nombres !== null ? (float) $obj->value_nombres : null,
                'value_volume' => $obj->value_volume !== null ? (float) $obj->value_volume : null,
                'period' => $obj->period,
                'year' => (int) $obj->year,
                'month' => $obj->month !== null ? (int) $obj->month : null,
                'quarter' => $obj->quarter !== null ? (int) $obj->quarter : null,
                'status' => $obj->status,
                'description' => $obj->description,
            ];
        }

        return array_values($byType);
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
