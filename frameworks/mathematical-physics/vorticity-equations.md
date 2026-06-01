# Vorticity Equations in Navier-Stokes

## Definition
Vorticity \(\omega\) is defined as the curl of the velocity field:
\[
\omega = \nabla \times \mathbf{u}
\]

## Vorticity Equation
For incompressible Navier-Stokes equations:
\[
\partial_t \mathbf{u} + (\mathbf{u} \cdot \nabla) \mathbf{u} = -\nabla p + \nu \Delta \mathbf{u}
\]
\[
\nabla \cdot \mathbf{u} = 0
\]

Taking the curl of the momentum equation yields the vorticity equation:
\[
\frac{D\omega}{Dt} = (\omega \cdot \nabla) \mathbf{u} + \nu \Delta \omega
\]
where \(\frac{D}{Dt} = \partial_t + \mathbf{u} \cdot \nabla\) is the material derivative.

## Components
- **Advection**: \(\mathbf{u} \cdot \nabla \omega\) - transport of vorticity by the flow
- **Stretching**: \((\omega \cdot \nabla) \mathbf{u}\) - stretching/amplification of vorticity
- **Diffusion**: \(\nu \Delta \omega\) - viscous dissipation

## Key Properties
- Vorticity is divergence-free: \(\nabla \cdot \omega = 0\)
- In 2D, the stretching term vanishes, leading to different behavior
- The stretching term can amplify vorticity exponentially in 3D

## Relation to Smoothness
Smoothness breakdown would manifest as infinite vorticity concentration. The stretching term provides a mechanism for this, while diffusion counteracts it.

## Analysis Techniques
- Maximum principles for vorticity
- Enstrophy (L^2 norm of vorticity) evolution
- Helicity conservation (in inviscid case)

## Tao's Contribution
Tao's 2016 paper uses vorticity estimates in critical Besov spaces to control the nonlinear terms and prevent blow-up for small data.