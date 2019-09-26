import setuptools

with open("README.md") as readme:
    long_desc = readme.read()

setuptools.setup(
    name="dbus-codegen",
    version="0.0.1",
    author="Emil Tylén",
    author_email="emil.tylen@grepit.se",
    description="Generate Python code from DBus introspection data",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/skf/python-dbus-codegen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.5",
)
