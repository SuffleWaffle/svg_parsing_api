import os

# ________________________________________________________________________________
# --- APPLICATION SETTINGS ---
PARALLEL_PROC_TIMEOUT: int = int(os.getenv("PARALLEL_PROC_TIMEOUT"))

AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY")
AWS_REGION_NAME: str = os.getenv("AWS_REGION_NAME")

# ________________________________________________________________________________
# --- ALGORITHM SETTINGS ---
SVG_ELEMENTS_EXTRACTION = dict(extract_svg_cub_bezier_lines=dict(interpolation_t=20))
ROUND_THRESHOLD = 0.1
