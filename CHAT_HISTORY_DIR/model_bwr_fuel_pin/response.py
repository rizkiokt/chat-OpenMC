import openmc

# Define materials (enrichments and densities are approximate)
# -----------------------------------------------------------------------------

# Fuel (UO2 with 4.9% enrichment and 6% Gd2O3)
fuel = openmc.Material(name='Fuel')
fuel.add_nuclide('U235', 4.9e-2)  # 4.9% enrichment
fuel.add_nuclide('U238', (1 - 4.9e-2) - (6e-2 * 152/272)) # Rest U238 minus Gd
fuel.add_nuclide('O16', 2.0)
fuel.add_nuclide('Gd155', 6e-2 * 0.1481/152)  # Gd composition based on natural abundance
fuel.add_nuclide('Gd157', 6e-2 * 0.1564/152)
fuel.set_density('g/cm3', 10.4) # Typical UO2 density, adjust if needed


# Zircaloy-4 Cladding
clad = openmc.Material(name='Cladding')
clad.add_nuclide('Zr90', 0.5145)
clad.set_density('g/cm3', 6.55)

# Borated Water
hot_water = openmc.Material(name='Borated Water')
hot_water.add_nuclide('H1', 2)
hot_water.add_nuclide('O16', 1)
hot_water.add_nuclide('B10', 8.0042e-6) # Example boron concentration, adjust if needed
hot_water.add_nuclide('B11', 3.2218e-5)
hot_water.set_density('g/cm3', 0.74)
hot_water.add_s_alpha_beta('c_H_in_H2O')

# Define geometry
# -----------------------------------------------------------------------------

# Pin dimensions (using typical BWR values. Adjust as needed).
fuel_or = openmc.ZCylinder(r=0.54) # Fuel outer radius
clad_or = openmc.ZCylinder(r=0.62) # Cladding outer radius

# Define pincell height and boundary planes
pincell_height = 1.26 # Example height. Adjust as needed.
min_z = openmc.ZPlane(z0=-pincell_height/2, boundary_type='reflective')
max_z = openmc.ZPlane(z0=+pincell_height/2, boundary_type='reflective')


# Create pin cell universe
fuel_cell = openmc.Cell(fill=fuel, region=-fuel_or & +min_z & -max_z)
clad_cell = openmc.Cell(fill=clad, region=+fuel_or & -clad_or & +min_z & -max_z)
hot_water_cell = openmc.Cell(fill=hot_water, region=+clad_or & +min_z & -max_z)


pincell = openmc.Universe(name='BWR Pincell')
pincell.add_cells([fuel_cell, clad_cell, hot_water_cell])

# Create a root universe and add the pincell
root_universe = openmc.Universe(universe_id=0, name='root universe')
root_cell = openmc.Cell(fill=pincell)
root_universe.add_cell(root_cell)


# Define geometry and export to XML
# -----------------------------------------------------------------------------
geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()


# Define materials and export to XML
# -----------------------------------------------------------------------------
materials = openmc.Materials([fuel, clad, hot_water])
materials.export_to_xml()


# Settings (Example. Adjust as per your needs)
# -----------------------------------------------------------------------------
settings = openmc.Settings()
settings.run_mode = "eigenvalue"
settings.particles = 10000
settings.batches = 100
settings.inactive = 10
settings.export_to_xml()


#  Tallies (Example. Define your tallies as needed)
# -----------------------------------------------------------------------------

tallies = openmc.Tallies()

# Example flux tally (Modify/Add as needed)
mesh = openmc.RegularMesh()
mesh.dimension = [1, 1, 1]  # 1x1x1 mesh
mesh.lower_left = [-0.62, -0.62, -pincell_height/2]
mesh.width = [1.24, 1.24, pincell_height]
mesh_filter = openmc.MeshFilter(mesh)

flux_tally = openmc.Tally(name='flux')
flux_tally.filters = [mesh_filter]
flux_tally.scores = ['flux']
tallies.append(flux_tally)


tallies.export_to_xml()

openmc.run()

print("OpenMC input files generated and simulation completed.")