import sys
import os

# Garante que o diretório raiz do projeto esteja no PYTHONPATH,
# permitindo que os imports de módulos (sources, filters, storage, etc.)
# funcionem corretamente tanto localmente quanto no GitHub Actions.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
