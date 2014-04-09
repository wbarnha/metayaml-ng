from setuptools import setup

setup(
    name="metayaml",
    version="0.6",
    author="Anton Tagunov",
    packages=["metayaml"],
    package_data={'': ['test_files/*.yaml']},
    url="https://bitbucket.org/atagunov/metayaml/",
    description="Enhancements of yaml format to support include and python expression",
    long_description=open('README.rst').read(),
    install_requires=['jinja2', 'PyYAML'],
    extras_require={
        'test': ['attrdict'],
    },
    include_package_data=True,
)
