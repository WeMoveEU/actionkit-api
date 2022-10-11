from setuptools import setup, find_packages

setup(
    name="actionkit",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["Click", "requests", "requests-toolbelt"],
    # entry_points={
    #     "console_scripts": [
    #         "donation-import=actionkit.scripts.donation-import:cli",
    #     ],
    # },
)
