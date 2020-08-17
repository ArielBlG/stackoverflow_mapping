import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stackoverflow_java_queries",
    version="0.1.2",
    author="Ariel",
    author_email="arielblobstein@gmail.com",
    description="Stack Overflow java queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ArielBlG/stackoverflow_java_queries",
    packages=setuptools.find_packages(),
    install_requires=['pandas>=1.0.5','javalang>=0.13.0','google-cloud-bigquery>=1.25.0',],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)