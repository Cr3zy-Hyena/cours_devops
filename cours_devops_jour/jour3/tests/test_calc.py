import sys
from pathlib import Path
import pytest

# Ajouter le dossier `jour3` au PYTHONPATH pour importer `calc` depuis les tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calc import calculate


def test_add():
    assert calculate(3, 2, 'add') == 5


def test_sub():
    assert calculate(3, 2, 'sub') == 1


def test_mul():
    assert calculate(3, 2, 'mul') == 6


def test_div():
    assert calculate(6, 2, 'div') == 3


def test_division_by_zero():
    res = calculate(1, 0, 'div')
    assert isinstance(res, dict) and res.get('error') == 'Division par zéro'
