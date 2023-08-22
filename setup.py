from setuptools import setup, find_packages

setup(
    name="actionkit",
    version="0.2.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests", "requests-toolbelt"],
)
