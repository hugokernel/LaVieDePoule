# -*- coding: utf8 -*-

lux_map = ('nuit', 'beau temps', 'super beau temps')

sensors_map = ('enceinte', 'extérieur', 'nid 1', 'nid 2')

report = '%s, lumière: %s, (alim %0.1fV@%0.1fA)'

record_out_temp_min = "Record de température extérieure basse atteint avec %0.1f°C %s !"
record_out_temp_max = "Record de température extérieure haute atteint avec %0.1f°C %s !"

stats_yesterday = "Stats d'hier (%s) #statsjour"
stats_lastweek = "Stats de la semaine passée (semaine %s) #statssemaine"
stats_lastmonth = "Stats du mois passée (%s) #statsmois"

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
    (1, 'la basse-cour'),
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

