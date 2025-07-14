#!/usr/bin/env python
"""
Script pour exécuter tous les tests de l'application SGQ Ligne G

Usage:
    python run_tests.py              # Exécuter tous les tests
    python run_tests.py core         # Tests de l'app core uniquement
    python run_tests.py -v 2         # Mode verbose
    python run_tests.py --failfast   # Arrêter au premier échec
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'SGQ_LigneG.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Récupérer les arguments
    test_labels = []
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            test_labels.append(arg)
    
    # Si aucun test spécifié, exécuter tous les tests
    if not test_labels:
        test_labels = [
            'core.tests',
            'production.tests',
            'livesession.tests',
            'livesession.test_services',
        ]
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        sys.exit(bool(failures))