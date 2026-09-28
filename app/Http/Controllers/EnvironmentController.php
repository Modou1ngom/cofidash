<?php

namespace App\Http\Controllers;

use App\Models\Environment;
use Illuminate\Http\Request;

class EnvironmentController extends Controller
{
    public function index()
    {
        return response()->json(
            Environment::withCount('agencies')->orderBy('name')->get()
        );
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:120|unique:environments,name',
        ]);

        $environment = Environment::create([
            'name' => mb_strtoupper(trim($validated['name'])),
        ]);

        return response()->json($environment->loadCount('agencies'), 201);
    }

    public function update(Request $request, Environment $environment)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:120|unique:environments,name,' . $environment->id,
        ]);

        $environment->update([
            'name' => mb_strtoupper(trim($validated['name'])),
        ]);

        return response()->json($environment->loadCount('agencies'));
    }

    public function destroy(Environment $environment)
    {
        $environment->delete();

        return response()->json(['message' => 'Environnement supprimé']);
    }

    public function agencies(Environment $environment)
    {
        $agencies = $environment->agencies()
            ->with('territory')
            ->orderBy('name')
            ->get(['id', 'code', 'name', 'territory_id', 'environment_id']);

        return response()->json($agencies);
    }
}
