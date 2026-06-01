# PDE Analysis of Navier-Stokes Equations

## Equation Form
The incompressible Navier-Stokes equations:
\[
\partial_t \mathbf{u} + \mathbf{u} \cdot \nabla \mathbf{u} = -\nabla p + \nu \Delta \mathbf{u}
\]
\[
\nabla \cdot \mathbf{u} = 0
\]

## Mathematical Properties
- **Quasilinear**: Nonlinearity depends on the solution.
- **Parabolic**: The viscous term provides smoothing.
- **Nonlocal**: Pressure determined by elliptic equation from divergence.

## Regularity Theory
- **Local Existence**: Smooth solutions exist locally in time for smooth initial data.
- **Global Existence**: Open problem for 3D.
- **Uniqueness**: Unique for weak solutions in appropriate spaces.

## Key Estimates
- **Energy Inequality**: \(\frac{1}{2} \frac{d}{dt} \|\mathbf{u}\|^2 + \nu \|\nabla \mathbf{u}\|^2 = 0\)
- **Enstrophy**: \(\frac{d}{dt} \|\omega\|^2 + 2\nu \|\nabla \omega\|^2 \leq 0\) (inviscid: conserved)

## Tao's Analysis
- Uses Besov spaces for critical scaling.
- Proves that small data in \(F^{-1}_{\infty,\infty}\) leads to global regularity.
- Employs contradiction argument assuming blow-up.

## Potential Breakdown Mechanisms
- **Nonlinear Term**: \(\mathbf{u} \cdot \nabla \mathbf{u}\) can create high frequencies.
- **Vorticity Stretching**: Amplifies gradients.
- **Pressure**: Nonlocal effects.

## Scaling
Critical exponents: velocity scales as L/T, time as L^2/ν, etc.
Critical Sobolev index s = 1/2 for u in H^s.

## Open Questions
- Does blow-up occur for large data?
- What is the minimal regularity for uniqueness?