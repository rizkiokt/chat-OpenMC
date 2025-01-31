import openmc

# Materials
fuel = openmc.Material(1, name="UO2 Fuel")
fuel.add_nuclide("U235", 0.045) # Enriched UO2
fuel.add_nuclide("U238", 1.0 - 0.045)
fuel.add_element("O", 2.0)
fuel.set_density("g/cm3", 10.3)

gap = openmc.Material(2, name="Gap")
gap.add_nuclide("Xe135", 1.0) # Placeholder; replace with actual gap composition
gap.set_density("g/cm3", 0.001)

clad = openmc.Material(3, name="Zircaloy Cladding")
clad.add_nuclide("Zr90", 0.5145) # Simplified Zircaloy composition; replace with more accurate data
clad.add_nuclide("Zr91", 0.1122)
clad.add_nuclide("Zr92", 0.1715)
clad.add_nuclide("Zr94", 0.1738)
clad.add_nuclide("Zr96", 0.0280)
clad.set_density("g/cm3", 6.55)


water = openmc.Material(4, name="Water")
water.add_nuclide("H1", 2.0)
water.add_nuclide("O16", 1.0)
water.set_density("g/cm3", 1.0)


materials = openmc.Materials([fuel, gap, clad, water])


# Geometry
fuel_radius = 0.40  # cm
gap_radius = 0.41 #cm
clad_radius = 0.47  # cm
pitch = 1.26 # cm

# Create surfaces
fuel_outer = openmc.ZCylinder(R=fuel_radius)
gap_outer = openmc.ZCylinder(R=gap_radius)
clad_outer = openmc.ZCylinder(R=clad_radius)

# Create cells
fuel_cell = openmc.Cell(1)
fuel_cell.fill = fuel
fuel_cell.region = -fuel_outer

gap_cell = openmc.Cell(2)
gap_cell.fill = gap
gap_cell.region = +fuel_outer & -gap_outer

clad_cell = openmc.Cell(3)
clad_cell.fill = clad
clad_cell.region = +gap_outer & -clad_outer

moderator_cell = openmc.Cell(4)
moderator_cell.region = +clad_outer
moderator_cell.fill = water

# Create a universe for the pin cell
root_universe = openmc.Universe(cells=(fuel_cell, gap_cell, clad_cell, moderator_cell))

# Geometry
geometry = openmc.Geometry(root_universe)


# Settings
settings = openmc.Settings()
settings.batches = 100
settings.inactive = 10
settings.particles = 20000
settings.source = openmc.Source(space=openmc.stats.Box((-pitch/2,-pitch/2,-1),(pitch/2,pitch/2,1))) #Volume source


# Export to XML
materials.export_to_xml()
geometry.export_to_xml()
settings.export_to_xml()

# Run OpenMC
openmc.run()