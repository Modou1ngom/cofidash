<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>COFIdash</title>
    <link rel="icon" type="image/png" href="/logo.png">
    <style>
        /* Styles critiques - garantissent le même rendu dev/prod */
        html, body { margin: 0; padding: 0; width: 100%; min-height: 100%; overflow-x: hidden; box-sizing: border-box; }
        #app { width: 100%; min-height: 100vh; display: block; }
        *, *::before, *::after { box-sizing: border-box; }
    </style>
    @vite(['resources/js/app.js'])
</head>
<body>
    <div id="app"></div>
</body>
</html>

