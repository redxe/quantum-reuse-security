"""Example: exact Quirk-sequence coherent teleportation cleanup check."""

import numpy as np

from quantum_reuse.circuits import coherent_teleportation_cleanup_quirk


if __name__ == "__main__":
    psi = np.array([1.0, 1.0j], dtype=complex)
    psi /= np.linalg.norm(psi)

    out = coherent_teleportation_cleanup_quirk(psi)
    print("Output amplitudes for |0,0,psi> state:")
    print(out)
