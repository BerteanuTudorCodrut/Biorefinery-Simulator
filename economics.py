def calculate_economics(product,
                        total_energy,
                        co2,
                        biomass_flow,
                        feedstock_price,
                        product_price=1.2,
                        electricity_price=0.18,
                        carbon_price=80):

    revenue = product * product_price

    energy_cost = total_energy * electricity_price

    carbon_cost = co2 * carbon_price / 1000

    feedstock_cost = biomass_flow/1000 * feedstock_price

    profit = revenue - energy_cost - carbon_cost - feedstock_cost

    return revenue, energy_cost, carbon_cost, feedstock_cost, profit
