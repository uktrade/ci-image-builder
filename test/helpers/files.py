import json


def create_nodejs_indicator(fs, version):
    fs.create_file(
        "package.json",
        contents=json.dumps(
            {
                "engines": {
                    "node": version,
                },
            }
        ),
    )


def create_python_indicator(fs, version, indicator_type="pyproject"):
    if indicator_type == "pyproject":
        fs.create_file(
            "pyproject.toml",
            contents=f'[tool.poetry.dependencies]\npython = "{version}"',
        )
    if indicator_type == "runtime":
        fs.create_file("runtime.txt", contents=f"python-{version}.x")


def create_ruby_indicator(fs, version):
    fs.create_file("Gemfile", contents=f"ruby {version}")
