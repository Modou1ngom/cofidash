<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Versions de l'app mobile (COFINA CLIENT VUE 360)
    |--------------------------------------------------------------------------
    |
    | latest_version : dernière version publiée (proposition de MAJ)
    | min_version    : version minimale acceptée (en dessous = force update)
    | force_update   : forcer la MAJ même si >= min_version
    |
    */
    'latest_version' => env('MOBILE_LATEST_VERSION', '1.0.0'),
    'min_version' => env('MOBILE_MIN_VERSION', '1.0.0'),
    'force_update' => (bool) env('MOBILE_FORCE_UPDATE', false),
    'store_url_android' => env(
        'MOBILE_STORE_URL_ANDROID',
        'https://play.google.com/store/apps/details?id=com.cofina.cofina_client_vue360'
    ),
    'store_url_ios' => env(
        'MOBILE_STORE_URL_IOS',
        'https://apps.apple.com/app/id0000000000'
    ),
    'message' => env(
        'MOBILE_UPDATE_MESSAGE',
        'Une nouvelle version de l\'application est disponible.'
    ),
];
