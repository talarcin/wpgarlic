import json
import subprocess

output = subprocess.run(
    ["composer", "install"]
)

print(json.dumps(output))
