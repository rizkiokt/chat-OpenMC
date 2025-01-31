import openmc

# ... (Material and Geometry definitions from the previous responses remain unchanged) ...

# Define materials file and export to XML.  No cross_sections assignment needed here!
materials_file = openmc.Materials([fuel, clad, hot_water])
materials_file.export_to_xml()


# ... (Settings and openmc.run() remain unchanged)