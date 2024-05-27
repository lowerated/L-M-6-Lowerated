import json

# Read the file content
file_path = 'sbr'
output_json_path = 'entities.json'

with open(file_path, 'r') as file:
    lines = file.readlines()

# Initialize variables
entities = {}
current_entity = None

# Process each line to extract entities and their attributes
for line in lines:
    line = line.strip()
    if line.startswith("####"):
        current_entity = line.replace("####", "").strip()
        entities[current_entity] = []
    elif line.startswith(tuple(f"{i}. **" for i in range(1, 8))) and current_entity:
        attribute = line.split("**")[1].split("-")[0].strip()
        entities[current_entity].append(attribute)

# Sort the entities alphabetically
sorted_entities = {entity: attributes for entity,
                   attributes in sorted(entities.items())}

# Convert the sorted entities to a JSON object
sorted_entities_json = json.dumps(sorted_entities, indent=4)

# Write the JSON object to a file
with open(output_json_path, 'w') as json_file:
    json_file.write(sorted_entities_json)

print(f"Sorted entities have been written to {output_json_path}")
