import json
from pathlib import Path

GAME = json.loads((Path(__file__).parent / "game_data.json").read_text())
