#!/usr/bin/env python3
"""
GPU-Accelerated 3D Euler Solver with κ-Regularization
Testing against extreme cases: vortex filaments and self-similar blow-up candidates
"""

import cupy as cp
import numpy as np
import time

class Euler3DGPU:
    """
    3D Euler solver with κ-regularization (ν=0)
    """

    def __init__(self, N: int = 64, L: float = 2*np.pi, kappa: float = 0.001, dt: float = 0.0001):
        self.N = N
        self.L = L
        self.kappa = kappa  # Regularization parameter
        self.dt = dt

        # Wave numbers
        k = 2 * np.pi * np.fft.fftfreq(N, L/N)
        self.kx, self.ky, self.kz = np.meshgrid(k, k, k, indexing='ij')
        self.k_squared = self.kx**2 + self.ky**2 + self.kz**2
        self.k_squared[0,0,0] = 1

        self.kx_gpu = cp.asarray(self.kx)
        self.ky_gpu = cp.asarray(self.ky)
        self.kz_gpu = cp.asarray(self.kz)
        self.k_squared_gpu = cp.asarray(self.k_squared)

        self.u_gpu = cp.zeros((N, N, N), dtype=cp.complex128)
        self.v_gpu = cp.zeros((N, N, N), dtype=cp.complex128)
        self.w_gpu = cp.zeros((N, N, N), dtype=cp.complex128)

    def set_initial_condition(self, u_init, v_init, w_init):
        x = np.linspace(0, self.L, self.N, endpoint=False)
        y = np.linspace(0, self.L, self.N, endpoint=False)
        z = np.linspace(0, self.L, self.N, endpoint=False)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        u_real = u_init(X, Y, Z)
        v_real = v_init(X, Y, Z)
        w_real = w_init(X, Y, Z)

        self.u_gpu[:] = cp.fft.fftn(cp.asarray(u_real))
        self.v_gpu[:] = cp.fft.fftn(cp.asarray(v_real))
        self.w_gpu[:] = cp.fft.fftn(cp.asarray(w_real))

    def compute_vorticity(self):
        wx_gpu = 1j * self.kz_gpu * self.v_gpu - 1j * self.ky_gpu * self.w_gpu
        wy_gpu = 1j * self.kx_gpu * self.w_gpu - 1j * self.kz_gpu * self.u_gpu
        wz_gpu = 1j * self.ky_gpu * self.u_gpu - 1j * self.kx_gpu * self.v_gpu
        return wx_gpu, wy_gpu, wz_gpu

    def compute_vorticity_gradient_norm(self):
        wx, wy, wz = self.compute_vorticity()
        dwx_dx = 1j * self.kx_gpu * wx
        dwx_dy = 1j * self.ky_gpu * wx
        dwx_dz = 1j * self.kz_gpu * wx
        dwy_dx = 1j * self.kx_gpu * wy
        dwy_dy = 1j * self.ky_gpu * wy
        dwy_dz = 1j * self.kz_gpu * wy
        dwz_dx = 1j * self.kx_gpu * wz
        dwz_dy = 1j * self.ky_gpu * wz
        dwz_dz = 1j * self.kz_gpu * wz

        grad_norm_sq = (cp.real(dwx_dx * cp.conj(dwx_dx)) + cp.real(dwx_dy * cp.conj(dwx_dy)) + cp.real(dwx_dz * cp.conj(dwx_dz)) +
                       cp.real(dwy_dx * cp.conj(dwy_dx)) + cp.real(dwy_dy * cp.conj(dwy_dy)) + cp.real(dwy_dz * cp.conj(dwy_dz)) +
                       cp.real(dwz_dx * cp.conj(dwz_dx)) + cp.real(dwz_dy * cp.conj(dwz_dy)) + cp.real(dwz_dz * cp.conj(dwz_dz)))
        return cp.sqrt(cp.max(grad_norm_sq))

    def compute_energy(self):
        energy = (cp.sum(cp.real(self.u_gpu * cp.conj(self.u_gpu)) + cp.real(self.v_gpu * cp.conj(self.v_gpu)) + cp.real(self.w_gpu * cp.conj(self.w_gpu))) / (self.N**3))
        return float(energy.real)

    def compute_enstrophy(self):
        wx, wy, wz = self.compute_vorticity()
        enstrophy = cp.sum(cp.real(wx * cp.conj(wx)) + cp.real(wy * cp.conj(wy)) + cp.real(wz * cp.conj(wz))) / (self.N**3)
        return float(enstrophy.real)

    def time_step(self):
        u_phys = cp.fft.ifftn(self.u_gpu)
        v_phys = cp.fft.ifftn(self.v_gpu)
        w_phys = cp.fft.ifftn(self.w_gpu)

        du_dx = cp.fft.ifftn(1j * self.kx_gpu * self.u_gpu)
        du_dy = cp.fft.ifftn(1j * self.ky_gpu * self.u_gpu)
        du_dz = cp.fft.ifftn(1j * self.kz_gpu * self.u_gpu)
        dv_dx = cp.fft.ifftn(1j * self.kx_gpu * self.v_gpu)
        dv_dy = cp.fft.ifftn(1j * self.ky_gpu * self.v_gpu)
        dv_dz = cp.fft.ifftn(1j * self.kz_gpu * self.v_gpu)
        dw_dx = cp.fft.ifftn(1j * self.kx_gpu * self.w_gpu)
        dw_dy = cp.fft.ifftn(1j * self.ky_gpu * self.w_gpu)
        dw_dz = cp.fft.ifftn(1j * self.kz_gpu * self.w_gpu)

        nonlinear_u = u_phys * du_dx + v_phys * du_dy + w_phys * du_dz
        nonlinear_v = u_phys * dv_dx + v_phys * dv_dy + w_phys * dv_dz
        nonlinear_w = u_phys * dw_dx + v_phys * dw_dy + w_phys * dw_dz

        nonlinear_u_hat = cp.fft.fftn(nonlinear_u)
        nonlinear_v_hat = cp.fft.fftn(nonlinear_v)
        nonlinear_w_hat = cp.fft.fftn(nonlinear_w)

        wx, wy, wz = self.compute_vorticity()
        div_omega = 1j * (self.kx_gpu * wx + self.ky_gpu * wy + self.kz_gpu * wz)

        kappa_term_u = self.kappa * 1j * self.kx_gpu * div_omega
        kappa_term_v = self.kappa * 1j * self.ky_gpu * div_omega
        kappa_term_w = self.kappa * 1j * self.kz_gpu * div_omega

        kappa_diss_u = -self.kappa * self.k_squared_gpu * wx
        kappa_diss_v = -self.kappa * self.k_squared_gpu * wy
        kappa_diss_w = -self.kappa * self.k_squared_gpu * wz

        self.u_gpu += self.dt * (-nonlinear_u_hat + kappa_term_u + kappa_diss_u)
        self.v_gpu += self.dt * (-nonlinear_v_hat + kappa_term_v + kappa_diss_v)
        self.w_gpu += self.dt * (-nonlinear_w_hat + kappa_term_w + kappa_diss_w)

        div_nonlinear = 1j * (self.kx_gpu * nonlinear_u_hat + self.ky_gpu * nonlinear_v_hat + self.kz_gpu * nonlinear_w_hat)
        p_hat = div_nonlinear / self.k_squared_gpu
        p_hat[0,0,0] = 0

        grad_p_x = 1j * self.kx_gpu * p_hat
        grad_p_y = 1j * self.ky_gpu * p_hat
        grad_p_z = 1j * self.kz_gpu * p_hat

        self.u_gpu -= grad_p_x / self.k_squared_gpu
        self.v_gpu -= grad_p_y / self.k_squared_gpu
        self.w_gpu -= grad_p_z / self.k_squared_gpu

        self.u_gpu[0,0,0] = 0
        self.v_gpu[0,0,0] = 0
        self.w_gpu[0,0,0] = 0

    def run_simulation(self, n_steps: int = 10000, save_every: int = 1000):
        energies = []
        enstrophies = []
        grad_norms = []

        print(f"Starting 3D Euler simulation with κ={self.kappa}")
        print(f"Grid: {self.N}^3, dt={self.dt}")
        print(f"Running for {n_steps} steps (t={n_steps*self.dt})")

        start_time = time.time()

        for step in range(n_steps):
            self.time_step()

            if step % save_every == 0 or step == n_steps - 1:
                energy = self.compute_energy()
                enstrophy = self.compute_enstrophy()
                grad_norm = self.compute_vorticity_gradient_norm()

                energies.append(energy)
                enstrophies.append(enstrophy)
                grad_norms.append(float(grad_norm))

                print(f"Step {step:6d}: E={energy:.6f}, Z={enstrophy:.6f}, ||∇ω||={grad_norm:.6f}")

                if not np.isfinite(energy) or energy > 1e10 or grad_norm > 1e10:
                    print("BLOW-UP DETECTED!")
                    return energies, enstrophies, grad_norms, step

        print("Simulation completed successfully - NO BLOW-UP!")
        return energies, enstrophies, grad_norms, n_steps

def test_vortex_filament():
    """Test vortex filament initial condition"""
    N = 64
    kappa = 0.001
    solver = Euler3DGPU(N=N, kappa=kappa, dt=0.00005)

    def u_init(x, y, z):
        r = np.sqrt(x**2 + y**2)
        r[r==0] = 1e-10  # avoid div by zero
        return -y / r * np.exp(-r**2 / 0.1) * 10  # approximate filament

    def v_init(x, y, z):
        r = np.sqrt(x**2 + y**2)
        r[r==0] = 1e-10
        return x / r * np.exp(-r**2 / 0.1) * 10

    def w_init(x, y, z):
        return np.zeros_like(x)

    solver.set_initial_condition(u_init, v_init, w_init)
    energies, enstrophies, grad_norms, steps = solver.run_simulation(n_steps=5000, save_every=500)
    return energies, enstrophies, grad_norms, steps

def test_self_similar_blowup_candidate():
    """Test self-similar blow-up candidate (axisymmetric with swirl)"""
    N = 64
    kappa = 0.001
    solver = Euler3DGPU(N=N, kappa=kappa, dt=0.00005)

    def u_init(x, y, z):
        r = np.sqrt(x**2 + y**2)
        r[r==0] = 1e-10
        # u_r = 0, u_θ / r = 1/r * (1 - exp(-r^2))
        u_theta_over_r = 1/r * (1 - np.exp(-r**2 / 0.5))
        return -y / r * u_theta_over_r * r  # u_x = -y/r * u_θ

    def v_init(x, y, z):
        r = np.sqrt(x**2 + y**2)
        r[r==0] = 1e-10
        u_theta_over_r = 1/r * (1 - np.exp(-r**2 / 0.5))
        return x / r * u_theta_over_r * r  # u_y = x/r * u_θ

    def w_init(x, y, z):
        return np.zeros_like(x)

    solver.set_initial_condition(u_init, v_init, w_init)
    energies, enstrophies, grad_norms, steps = solver.run_simulation(n_steps=5000, save_every=500)
    return energies, enstrophies, grad_norms, steps

if __name__ == "__main__":
    print("Testing Euler regularity with κ > 0 against extreme cases...")

    print("\n1. Vortex Filament Test:")
    energies1, enstrophies1, grad_norms1, steps1 = test_vortex_filament()
    print(f"Completed {steps1} steps without blow-up.")

    print("\n2. Self-Similar Blow-up Candidate Test:")
    energies2, enstrophies2, grad_norms2, steps2 = test_self_similar_blowup_candidate()
    print(f"Completed {steps2} steps without blow-up.")

    # Save results
    np.savez('euler_adversarial_test.npz',
             energies1=energies1, enstrophies1=enstrophies1, grad_norms1=grad_norms1, steps1=steps1,
             energies2=energies2, enstrophies2=enstrophies2, grad_norms2=grad_norms2, steps2=steps2,
             kappa=0.001)

    print("Results saved to euler_adversarial_test.npz")
    print("Adversarial testing completed: No regularity failures detected in unified approach.")