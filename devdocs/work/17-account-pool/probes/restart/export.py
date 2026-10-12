"""New export; preserve the failed r3 experiment exactly."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import export_prebuild
export_prebuild.EVIDENCE = Path(__file__).resolve().parents[2] / 'evidence/restart'
if __name__ == '__main__':
    export_prebuild.main()
