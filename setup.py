import setuptools
import versioneer

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PUMI",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Laboratory of Predictive Neuroimaging - University Hospital Essen, Germany",
    description="Nipype-based neuroimaging pipelines with a modular architecture.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)