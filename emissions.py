# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 12:25:26 2026

@author: Codrut
"""

def calculate_co2(energy_consumption, electricity_co2_factor):
    """
    Calculates CO2 emissions from energy consumption.
    """
    co2_emissions = energy_consumption * electricity_co2_factor
    return co2_emissions
