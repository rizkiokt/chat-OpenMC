import openmc

# Define materials (referencing external cross_sections.xml)
# We assume the cross_sections.xml file is generated separately and contains 
# the necessary definitions for fuel, clad, and hot_water.  
# These materials will include the appropriate nuclides and densities.

materials_file = openmc.Materials()
fuel = materials.get(name='fuel')
clad = materials.get(name='clad')
hot_water = materials.get(name='hot_water')




# Set enrichment and Gd content for fuel
# These values are assumed to be weight percentages.  The user needs to ensure
# their cross_sections.xml file is set up to handle these enrichments.
fuel.set_density('g/cm3') # ensure density is defined
enrichment = 0.049 # 4.9% enrichment
gad_content = 0.06 # 6% gadolinium content

# Adjust U235 and U238 atom fractions based on enrichment
fuel.remove_nuclide('U235')
fuel.remove_nuclide('U238')
fuel.add_nuclide('U235', enrichment * fuel.get_nuclide_atom_fraction('U') ) # Add U235 based on enrichment.  Assumes original material had some U.
fuel.add_nuclide('U238', (1 - enrichment) * fuel.get_nuclide_atom_fraction('U'))  # Add U238 to complete U content



# Add gadolinium. This assumes gadolinium is added as Gd2O3. *Clarify with the user if this is the correct form*
# This is a simplified representation and assumes the oxygen from Gd2O3 doesn't significantly displace other materials
# A more accurate representation might require adjusting other material fractions. 
fuel.add_element('Gd', gad_content * fuel.get_mass('g') / fuel.get_volume('cm3') / 157.25, 'wo') # Gd157.25 g/mol, 'wo' means percent weight of total


# Define geometry (based on standard BWR fuel pin dimensions from documentation)
fuel_or = openmc.ZCylinder(r=0.54) # Fuel outer radius
clad_or = openmc.ZCylinder(r=0.62) # Cladding outer radius

fuel_cell = openmc.Cell(fill=fuel, region=-fuel_or)
clad_cell = openmc.Cell(fill=clad, region=+fuel_or & -clad_or)
hot_water_cell = openmc.Cell(fill=hot_water, region=+clad_or)

pincell_universe = openmc.Universe(name='BWR Pincell')
pincell_universe.add_cells([fuel_cell, clad_cell, hot_water_cell])


# Create geometry and export to XML
geometry = openmc.Geometry(pincell_universe)
geometry.export_to_xml()


# Assuming materials.xml is already generated elsewhere
# with fuel, clad and hot_water definitions.
materials.export_to_xml()


# Create settings (using default settings for now)
settings = openmc.Settings()
settings.batches = 100
settings.inactive = 10
settings.particles = 1000
settings.export_to_xml()

#  Create tallies file and export to XML
tallies_file = openmc.Tallies()
tallies_file.export_to_xml()

print("OpenMC input files generated successfully.")