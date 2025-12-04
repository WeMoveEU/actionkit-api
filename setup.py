from setuptools import setup, find_packages

setup(
    name="actionkit",
    version="0.3.5",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests", "requests-toolbelt", "click>=8.0"],
    entry_points={
        "console_scripts": [
            "actionkit=actionkit.cli:main",
        ],
    },
)
