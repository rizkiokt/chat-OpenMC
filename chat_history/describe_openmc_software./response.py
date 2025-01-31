import openmc

# Materials
u235 = openmc.Material(material_id=1)
u235.add_nuclide('U235', 1.0) #1.0 represents 1 atom per molecule (pure U-235)
materials = openmc.Materials([u235])

# Geometry
sphere = openmc.Sphere(r=10, boundary_type='vacuum') #radius of 10cm
cell = openmc.Cell(fill=u235, region=-sphere)
universe = openmc.Universe(cells=[cell])
geometry = openmc.Geometry(universe)


# Settings
settings = openmc.Settings()
settings.batches = 10
settings.inactive = 5
settings.particles = 1000
settings.source = openmc.Source(space=openmc.stats.Point((0, 0, 0))) #point source at the center

# Export to XML
materials.export_to_xml()
geometry.export_to_xml()
settings.export_to_xml()