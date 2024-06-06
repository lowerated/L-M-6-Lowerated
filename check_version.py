import requests
import re
import sys


def get_version():
    with open('setup.py', 'r') as f:
        setup_content = f.read()
        version_match = re.search(
            r"version=['\"]([^'\"]+)['\"]", setup_content)
        if version_match:
            return version_match.group(1)
    raise ValueError("Could not find version in setup.py")


package_name = "lowerated"  # Replace with your package name
version = get_version()

response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
data = response.json()

if version in data["releases"]:
    print(f"Version {version} of {package_name} already exists on PyPI.")
    sys.exit(1)
else:
    print(f"Version {version} of {package_name} does not exist on PyPI.")
    sys.exit(0)
