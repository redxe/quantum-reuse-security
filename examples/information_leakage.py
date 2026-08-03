"""Example: print fixed-input fifth-wire leakage theorem summary."""

import json

from quantum_reuse.analysis import fixed_input_summary


if __name__ == "__main__":
    print(json.dumps(fixed_input_summary(), indent=2))
