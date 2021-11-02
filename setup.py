from setuptools import setup, find_packages


with open("VERSION") as version_file:
    version = version_file.read().strip()


setup(
    name="assh",
    version=version,
    packages=find_packages(),
    install_requires=["boto3~=1.9.85", "botostubs~=0.12", "Click~=7.0", "PyYAML~=5.3",],
    extras_require={
        "dev": [
            "black",
            "moto~=1.3.14",
            "pydocstyle~=5.0.2",
            "pytest~=5.3.5",
            "pytest-cov~=2.8.1",
            "pytest-mock~=2.0.0",
        ]
    },
    entry_points={"console_scripts": ["assh=assh.cli:main"]},
)
