# -*- coding: utf8 -*-

lux_map = ('nuit', 'beau temp', 'super beau temp')

sensors_map = ('extérieur', 'nid 1', 'nid 2')

#report = 'Temperatures -> enceinte: %0.2f°C, nid 1: %0.2f°C, nid 2: %0.2f°C, ext: %0.2f°C, tension: %0.2fV, courant: %0.2fA'
report = 'Temperatures -> enceinte: %0.2f°C, %s, luminosité: %s, tension: %0.2fV, courant: %0.2fA'
report_light = 'Temperature enceinte: %0.2f°C, luminosité: %0.2f, tension: %0.2fV, courant: %0.2fA'

cot = (
    '@%username% {0}',
    (
        (1, 'Cot'),
        (1, 'CotCot'),
        (1, 'CotCotCot'),
        (1, 'CotCot ?'),
        (1, 'Cot !'),
    )
)

enclos = (
    (1, 'la basse-court'),
    (1, 'l\'enclos')
)

garden_full = (
    '{0} {1} {2}',
    (
        (1, 'Cool !'),
        (1, 'Chouette !'),
        (1, 'Super !')
    ),
    (
        (1, 'On sort dans tout le jardin !'),
        (1, 'Openbar dans tout le jardin !'),
        (1, 'Accès au jardin, planquez-vous les vers, on arrive !')
    ),
    (
        (4, ''),
        (1, '#pétageDeBide')
    )
)

garden_close = (
    '{0}',
    (
        (1, 'On rentre du jardin après %time% !'),
        (1, 'Après %time% de {0} dans le jardin, on rentre !', (
            ( 1, 'folie' ),
            ( 1, 'délire' ),
            ( 1, 'repas' )
        )),
    )
)

garden_close_light = (
    '{0}',
    (
        (1, 'Toutes les bonnes choses ont une fin, nous rentrons du jardin !'),
        (1, 'Fini le jardin, on rentre !'),
    )
)

collect_egg = (
    '{0}',
    (
        (1, 'Collecte des oeufs ! La dernière date de %time_last% !'),
    )
)

collect_egg_light = (
    '{0}',
    (
        (1, 'Tiens, on vient collecter nos oeufs !'),
        (1, "C'est l'heure de la collecte des oeufs !"),
        (1, 'Hop, la main vient prendre nos oeufs !'),
    )
)

enclosure = (
    '{0}',
    (
        (1, 'Porte de {0} ouverte !', enclos),
        (1, '{0}, on peut sortir dans notre enclos !', (
            (1, 'Cotcot'),
            (1, 'Chouette')
        ))
    )
)

enclosure_close = (
    '{0}',
    (
        (1, 'Après %time%, on rentre de {0} !', enclos),
    )
)

enclosure_close_light = (
    '{0}',
    (
        (1, 'Fermeture de la porte de {0} !', enclos),
        (1, 'On rentre de {0} !', enclos),
    )
)

