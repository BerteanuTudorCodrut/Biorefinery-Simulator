# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 12:24:21 2026

@author: Codrut
"""

def calculate_mass_balance(biomass_flow, efficiency, energy_input, moisture=0):

    # Dry mass calculation
    dry_mass = biomass_flow * (1 - moisture)

    # Product + waste
    product = dry_mass * efficiency
    waste = dry_mass - product

    # Water removed during drying
    water_removed = biomass_flow * moisture

    # Drying energy (kWh)
    drying_energy = water_removed * 0.7

    # Total energy
    total_energy = energy_input + drying_energy

    energy_intensity = total_energy / product if product > 0 else 0

    return product, waste, energy_intensity, total_energy, drying_energy