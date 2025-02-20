import json
import pytest
from pathlib import Path

@pytest.fixture
def load_fixture():
    def _load_fixture(filename):
        fixture_path = Path(__file__).parent / 'fixtures' / f'{filename}.json'
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _load_fixture 