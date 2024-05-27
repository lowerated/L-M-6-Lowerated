# Read the file content
file_path = 'sbr'

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
        entities[current_entity].append(line)

# Sort the entities alphabetically
sorted_entities = sorted(entities.items())

# Print the sorted entities with their attributes
for entity, attributes in sorted_entities:
    print(f"#### {entity}")
    for attribute in attributes:
        print(attribute)
    print("\n")
