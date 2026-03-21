---
name: devs
description: Allows for the construction of discrete event system specification (DEVS) modules, it specifies its internal structure, components, connections, and resources with more information. Use when creating a DEVS module in any language or when giving proofs that involve DEVS modules.
---

DEVS atomic contains:
- $\delta_{internal}()$, an internal transition, that sets the output and edits the atomic's state.
- $\delta_{external}(elapsed, bag)$, an external transition trigered by an external event, called with the elapsed time since the last internal transition, and one or (in the case of parallel DEVS) multiple simultaneous inputs, edits the atomic's state but does not output
- $\delta_confluence(elapsed, bag)$, this function is called when both a $\delta_{internal}()$ and $\delta_{external}(elapsed, bag)$ would occur a the exact same instant. For simplicity it should only decide if $\delta_{internal}()$ or $\delta_{external}(elapsed, bag)$ edits the state first.
- $ta()$, returns a duration such that $\delta_{internal}()$ will be called after $ta()$ time units has elapsed since the last internal transition. $ta()$ does not edit the state
- $\lambda()$ returns the output, which is a single event or multiple simultaneous events for the case of parallel DEVS. $\lambda()$ does not edit the state.

In the literature there is a distinction between Mealy or Moore models for atomics. In this project all atomics are treated as Mealy. 

DEVS networks connect multiple atomics via ports, they can be input or output ports, and connect $lambda()$ to $\delta_{external}(...)$. The network developed in this project continues a single simulation step until all outputs are processed. This means that if a single step would take infinite time (i.e. there is a loop of atomics that takes 0 time to cycle), the atomic network is malformed.

References:
- A Discrete EVent system Simulator manual by Jim Nutaro (available as "A Discrete EVent system Simulator manual.pdf" in the references)
- Continuous System Simulation by Cellier and Kofman, Chapter 11 
- Theory of Modeling and Simulation Discrete Event and Iterative System Computational Foundations Third Edition, by Zeigler, Muzy and Kofman

