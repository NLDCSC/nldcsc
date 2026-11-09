project = "NLDCSC"
copyright = "2026, NLDCSC"
author = "NLDCSC"

extensions = [
    "myst_parser",
    "sphinx.ext.githubpages",
    "sphinx_copybutton",
]

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
exclude_patterns = ["build"]

html_theme = "furo"
html_title = "NLDCSC documentation"
html_static_path = []
html_theme_options = {
    "source_repository": "https://github.com/NLDCSC/nldcsc",
    "source_directory": "docs/source/",
    "navigation_with_keys": True,
}
