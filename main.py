# main.py

from process_model import calculate_mass_balance
from emissions import calculate_co2
import pandas as pd
import matplotlib.pyplot as plt

# --- Read CSV ---
df = pd.read_csv('data.csv')

# --- Prepare lists for results ---
product_list = []
waste_list = []
co2_list = []
energy_intensity_list = []
names = []

# --- Run calculations for each scenario ---
for index, row in df.iterrows():
    product, waste, energy_intensity = calculate_mass_balance(
        row['biomass_flow'], row['conversion_efficiency'], row['energy_consumption']
    )
    co2 = calculate_co2(row['energy_consumption'], row['electricity_co2_factor'])
    
    # Store results
    product_list.append(product)
    waste_list.append(waste)
    co2_list.append(co2)
    energy_intensity_list.append(energy_intensity)
    names.append(row['name'])
    
    # Print results
    print(f"=== {row['name']} ===")
    print(f"Product: {product} kg/h")
    print(f"Waste: {waste} kg/h")
    print(f"Energy intensity: {energy_intensity:.2f} kWh/kg")
    print(f"CO2 emissions: {co2} kg/h\n")

# --- PLOTS ---
# 1️⃣ Product vs Waste
plt.figure(figsize=(10, 6))
plt.bar(names, product_list, label='Product Yield (kg/h)', alpha=0.7)
plt.bar(names, waste_list, bottom=product_list, label='Waste (kg/h)', alpha=0.7)
plt.ylabel('Mass (kg/h)')
plt.title('Product vs Waste for Different Scenarios')
plt.legend()
plt.savefig('plots/product_waste.png')
plt.show()

# 2️⃣ CO2 emissions
plt.figure(figsize=(8, 5))
plt.plot(names, co2_list, marker='o', linestyle='-', color='red')
plt.ylabel('CO2 emissions (kg/h)')
plt.title('CO2 Emissions per Scenario')
plt.grid(True)
plt.savefig('plots/co2_emissions.png')
plt.show()

# 3️⃣ Energy intensity
plt.figure(figsize=(8, 5))
plt.plot(names, energy_intensity_list, marker='s', linestyle='--', color='green')
plt.ylabel('Energy intensity (kWh/kg product)')
plt.title('Energy Intensity per Scenario')
plt.grid(True)
plt.savefig('plots/energy_intensity.png')
plt.show()
