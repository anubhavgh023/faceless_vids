
VALID_ASPECT_RATIOS = {
    "9:16": {"height": 1024, "width": 576},  # Portrait
    "16:9": {"height": 576, "width": 1024},  # Landscape
    "1:1": {"height": 1024, "width": 1024},  # Square
}

aspect_ratio = "9:16"

# Validate aspect ratio
if aspect_ratio not in VALID_ASPECT_RATIOS:
    print(f"NOT FOUND: {aspect_ratio}")
else:
    print(f"FOUND: {aspect_ratio}")
    print(f"value: {VALID_ASPECT_RATIOS[aspect_ratio]}")
    print(f"height: {VALID_ASPECT_RATIOS[aspect_ratio]['height']}")
    print(f"weight: {VALID_ASPECT_RATIOS[aspect_ratio]['width']}")