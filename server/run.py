"""Application entry point."""
import sys
from pathlib import Path

# Add shared directory to Python path for LED manager imports
project_root = Path(__file__).parent.parent
shared_path = project_root / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from app import create_app
from app.config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
