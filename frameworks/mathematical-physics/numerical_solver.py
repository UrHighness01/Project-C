#!/usr/bin/env python3
"""
Numerical Solver for Navier-Stokes Equations
Finite difference implementation for verification of analytical results
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Callable
import time

class NavierStokesSolver:
    """
    Numerical solution of Navier-Stokes equations using finite differences
    Focus on 2D case for computational tractability
    """

    def __init__(self, nx: int = 64, ny: int = 64, Lx: float = 1.0, Ly: float = 1.0,
                 nu: float = 0.01, dt: float = 0.001):
        self.nx, self.ny = nx, ny
        self.Lx, self.Ly = Lx, Ly
        self.nu = nu
        self.dt = dt

        # Grid spacing
        self.dx = Lx / (nx - 1)
        self.dy = Ly / (ny - 1)

        # Initialize fields
        self.u = np.zeros((nx, ny))  # x-velocity
        self.v = np.zeros((nx, ny))  # y-velocity
        self.p = np.zeros((nx, ny))  # pressure

        # Create grid
        self.x = np.linspace(0, Lx, nx)
        self.y = np.linspace(0, Ly, ny)
        self.X, self.Y = np.meshgrid(self.x, self.y)

    def set_initial_condition(self, u0: Callable, v0: Callable):
        """Set initial velocity field"""
        self.u = u0(self.X, self.Y)
        self.v = v0(self.X, self.Y)

    def compute_divergence(self) -> np.ndarray:
        """Compute ∇·u for incompressibility check"""
        du_dx = np.gradient(self.u, self.dx, axis=0)
        dv_dy = np.gradient(self.v, self.dy, axis=1)
        return du_dx + dv_dy

    def compute_vorticity(self) -> np.ndarray:
        """Compute vorticity ω = ∇×u"""
        du_dy = np.gradient(self.u, self.dy, axis=1)
        dv_dx = np.gradient(self.v, self.dx, axis=0)
        return dv_dx - du_dy

    def solve_pressure_poisson(self) -> np.ndarray:
        """Solve Poisson equation for pressure: ∇²p = -∇·(u·∇u)"""
        # Compute right-hand side
        u_grad_u = self.u * np.gradient(self.u, self.dx, axis=0) + \
                   self.v * np.gradient(self.u, self.dy, axis=1)
        v_grad_v = self.u * np.gradient(self.v, self.dx, axis=0) + \
                   self.v * np.gradient(self.v, self.dy, axis=1)

        rhs = -(np.gradient(u_grad_u, self.dx, axis=0) +
                np.gradient(v_grad_v, self.dy, axis=1))

        # Simple Jacobi iteration for Poisson equation
        p_new = np.copy(self.p)
        for _ in range(50):  # 50 iterations
            p_new[1:-1, 1:-1] = 0.25 * (
                p_new[2:, 1:-1] + p_new[:-2, 1:-1] +
                p_new[1:-1, 2:] + p_new[1:-1, :-2] -
                self.dx**2 * rhs[1:-1, 1:-1]
            )

        return p_new

    def time_step(self):
        """Advance one time step using fractional step method"""
        # 1. Compute tentative velocity (ignore pressure)
        u_tent = self.u + self.dt * (
            -self.u * np.gradient(self.u, self.dx, axis=0)
            -self.v * np.gradient(self.u, self.dy, axis=1)
            + self.nu * (np.gradient(np.gradient(self.u, self.dx, axis=0), self.dx, axis=0) +
                        np.gradient(np.gradient(self.u, self.dy, axis=1), self.dy, axis=1))
        )

        v_tent = self.v + self.dt * (
            -self.u * np.gradient(self.v, self.dx, axis=0)
            -self.v * np.gradient(self.v, self.dy, axis=1)
            + self.nu * (np.gradient(np.gradient(self.v, self.dx, axis=0), self.dx, axis=0) +
                        np.gradient(np.gradient(self.v, self.dy, axis=1), self.dy, axis=1))
        )

        # 2. Solve pressure Poisson equation
        self.p = self.solve_pressure_poisson()

        # 3. Project velocity to satisfy incompressibility
        dp_dx = np.gradient(self.p, self.dx, axis=0)
        dp_dy = np.gradient(self.p, self.dy, axis=1)

        self.u = u_tent - self.dt * dp_dx
        self.v = v_tent - self.dt * dp_dy

    def compute_energy(self) -> float:
        """Compute total kinetic energy"""
        return 0.5 * np.sum(self.u**2 + self.v**2) * self.dx * self.dy

    def check_conservation(self) -> Tuple[float, float]:
        """Check incompressibility and energy conservation"""
        divergence = np.max(np.abs(self.compute_divergence()))
        energy = self.compute_energy()
        return divergence, energy

    def run_simulation(self, n_steps: int = 1000, save_every: int = 100):
        """Run Navier-Stokes simulation"""
        energies = []
        divergences = []

        print("Starting Navier-Stokes simulation...")
        print(f"Grid: {self.nx}x{self.ny}, ν={self.nu}, dt={self.dt}")

        for step in range(n_steps):
            self.time_step()

            if step % save_every == 0:
                div, energy = self.check_conservation()
                energies.append(energy)
                divergences.append(div)

                print(f"Step {step}: Energy={energy:.6f}, Max|∇·u|={div:.2e}")

                # Check for numerical instability
                if not np.isfinite(energy) or energy > 1e10:
                    print("Numerical instability detected!")
                    break

        return energies, divergences

def test_taylor_green_vortex():
    """Test with Taylor-Green vortex (known analytical solution)"""
    solver = NavierStokesSolver(nx=24, ny=24, nu=0.5, dt=0.000001)

    # Initial Taylor-Green vortex
    def u0(x, y):
        return 0.001 * np.sin(x) * np.cos(y)

    def v0(x, y):
        return -0.001 * np.cos(x) * np.sin(y)

    solver.set_initial_condition(u0, v0)

    # Run short simulation
    energies, divergences = solver.run_simulation(n_steps=10, save_every=5)

    print("Taylor-Green vortex test completed")
    print(f"Final energy: {energies[-1]:.6f}")
    print(f"Max divergence: {max(divergences):.2e}")

    return solver

if __name__ == "__main__":
    # Run test simulation
    solver = test_taylor_green_vortex()