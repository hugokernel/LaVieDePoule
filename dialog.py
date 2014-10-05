# -*- coding: utf8 -*-

report = 'Temperatures -> enceinte: %0.2f°C, nid 1: %0.2f°C, nid 2: %0.2f°C, ext: %0.2f°C, tension: %0.2fV, courant: %0.2fA'
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
        (1, 'Toutes les bonnes choses ont une fin !'),
        (1, 'On rentre du jardin après %time% !'),
        (1, 'Après %time% de {0} dans le jardin, on rentre !', (
            ( 1, 'folie' ),
            ( 1, 'délire' ),
            ( 1, 'repas' )
        )),
    )
)

collect_egg = (
    '{0} {1}',
    (
        (1, 'Tiens, on vient collecter nos oeufs !'),
        (1, "C'est l'heure de la collecte des oeufs !"),
        (1, 'Hop, la main vient prendre nos oeufs !'),
    ), (
        (1, 'La dernière date de %time_last% !'),
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
        (1, 'Fermeture de la porte de {0} !', enclos),
        (1, 'Après %time%, on rentre de {0} !', enclos),
    )
)

