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
        'Cot',
        'CotCot',
        'CotCotCot',
        'CotCot ?',
        'Cot !',
    )
)

enclos = (
    'la basse-cour',
    'l\'enclos'
)

garden_full = (
    '{0} {1} {2}',
    (
        'Cool !',
        'Chouette !',
        'Super !'
    ),
    (
        'On sort dans tout le jardin !',
        'Openbar dans tout le jardin !',
        'Accès au jardin, planquez-vous les vers, on arrive !'
    ),
    (
        (4, ''),
        (1, '#pétageDeBide')
    )
)

garden_close = (
    '{0}',
    (
        'On rentre du jardin après %time% !',
        ('Après %time% de {0} dans le jardin, on rentre !', (
            'folie',
            'délire',
            'repas'
        )),
    )
)

garden_close_light = (
    '{0}',
    (
        'Toutes les bonnes choses ont une fin, nous rentrons du jardin !',
        'Fini le jardin, on rentre !',
    )
)

collect_egg = (
    '{0}',
    (
        'Collecte des oeufs ! La dernière date de %time_last% !',
    )
)

collect_egg_light = (
    '{0}',
    (
        'Tiens, on vient collecter nos oeufs !',
        "C'est l'heure de la collecte des oeufs !",
        'Hop, la main vient prendre nos oeufs !',
    )
)

enclosure = (
    '{0}',
    (
        ('Porte de {0} ouverte !', enclos),
        ('{0}, on peut sortir dans notre enclos !', (
            ('Cotcot'),
            ('Chouette')
        ))
    )
)

enclosure_close = (
    '{0}',
    (
        ('Après %time%, on rentre de {0} !', enclos),
    )
)

enclosure_close_light = (
    '{0}',
    (
        ('Fermeture de la porte de {0} !', enclos),
        ('On rentre de {0} !', enclos),
    )
)

egg_detected = (
    '{0}',
    (
        'Un oeuf à été détecté !',
        'Alerte oeuf !',
        ('{0}, un oeuf !', (
            'Chic',
            'Chouette',
            'Super'
        )),
    )
)

eggs_detected = (
    '{0}',
    (
        '%count% oeufs ont été détectés !',
        'Alerte oeufs !',
        ('{0}, des oeufs !', (
            'Chic',
            'Chouette',
            'Super'
        )),
    )
)

