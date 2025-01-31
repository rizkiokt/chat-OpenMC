import openmc

# Define materials (from OpenMC documentation examples and modified for BWR)
# -----------------------------------------------------------------------------

# Fuel (UOX with 4.9% enrichment and 6% Gd2O3)
# Assumption: The 6% Gd content refers to weight percent of Gd2O3 in the fuel.
# Assumption: The remaining fuel is UO2.
# Assumption: The density of the UOX fuel mixture is 10.5 g/cm3. This needs confirmation from the user if precision is critical.

fuel = openmc.Material(name='UO2 + 6% Gd2O3 Fuel')
fuel.set_density('g/cm3', 10.5) 
fuel.add_element('U', 0.94 * 0.049, enrichment=4.9) # 4.9% enriched U
fuel.add_element('O', 2 * 0.94) # Oxygen in UO2
fuel.add_element('Gd', 2 * 0.06 / (157.25*2 + 16*3), 'wo') # Gd in Gd2O3 (6% by weight)
fuel.add_element('O', 3 * 0.06 / (157.25*2 + 16*3), 'wo') # Oxygen in Gd2O3

# Cladding (Zircaloy-2) - Typical composition for BWR fuel cladding
clad = openmc.Material(name='Zircaloy-2 Cladding')
clad.set_density('g/cm3', 6.55) # Typical value
clad.add_element('Zr', 0.985) # Mass fraction
clad.add_element('Sn', 0.0145)
clad.add_element('Fe', 0.00125)
clad.add_element('Cr', 0.001)
clad.add_element('Ni', 0.0005)

# Moderator (Borated Water) -  Typical BWR coolant
hot_water = openmc.Material(name='Borated Water')
hot_water.set_density('g/cm3', 0.74) # Typical value for BWR operating conditions
hot_water.add_nuclide('H1', 2.0)
hot_water.add_nuclide('O16', 1.0)
hot_water.add_nuclide('B10', 8.0042e-6)  # Example boration level, may need adjustment
hot_water.add_nuclide('B11', 3.2218e-5)


# Define geometry (from OpenMC documentation and modified for BWR)
# ---------------------------------------------------------------------------

# Assumption: Standard BWR fuel pin dimensions (needs confirmation from user)
fuel_or = openmc.ZCylinder(r=0.54) # Fuel outer radius (cm)
clad_or = openmc.ZCylinder(r=0.62) # Cladding outer radius (cm)

pitch = 1.26 # Pin cell pitch (cm).  Assumption: Square lattice

# Create boundary planes to define the pin cell extent
min_x = openmc.XPlane(x0=-pitch/2, boundary_type='reflective')
max_x = openmc.XPlane(x0=+pitch/2, boundary_type='reflective')
min_y = openmc.YPlane(y0=-pitch/2, boundary_type='reflective')
max_y = openmc.YPlane(y0=+pitch/2, boundary_type='reflective')



def fuel_pin():
    """Returns a BWR fuel pin universe."""

    fuel_cell = openmc.Cell(fill=fuel, region=-fuel_or)
    clad_cell = openmc.Cell(fill=clad, region=+fuel_or & -clad_or)
    hot_water_cell = openmc.Cell(fill=hot_water, region=+clad_or)

    univ = openmc.Universe(name='BWR Fuel Pin')
    univ.add_cells([fuel_cell, clad_cell, hot_water_cell])
    return univ

# Create the pincell universe and root cell
pincell = fuel_pin()
root_cell = openmc.Cell(fill=pincell, region=+min_x & -max_x & +min_y & -max_y)
root_universe = openmc.Universe(cells=[root_cell])


# Define settings
# -----------------------------------------------------------------------------

settings = openmc.Settings()
settings.run_mode = 'eigenvalue'
settings.batches = 100
settings.inactive = 10
settings.particles = 10000

# Create a uniform spatial source distribution over fissionable materials
bounds = [-pitch/2, -pitch/2, -1, pitch/2, pitch/2, 1] # Assuming a height of 2 cm
uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)
settings.source = openmc.Source(space=uniform_dist)


# Define tallies
# -----------------------------------------------------------------------------
tallies = openmc.Tallies()

# k-effective tally
cell_filter = openmc.CellFilter(root_cell)
tally = openmc.Tally(name='k-effective')
tally.filters = [cell_filter]
tally.scores = ['k-effective']
tallies.append(tally)


# Export to XML
# -----------------------------------------------------------------------------
materials = openmc.Materials([fuel, clad, hot_water])
materials.cross_sections = "mgxs.h5" # Replace with your cross-section library path!
materials.export_to_xml()

geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()

settings.export_to_xml()
tallies.export_to_xml()

# Run OpenMC
# -------------------------------------
# openmc.run() # Uncomment to run OpenMC after filling the cross_sections path