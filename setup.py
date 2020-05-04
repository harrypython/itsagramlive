import setuptools

project_homepage = "https://github.com/harrypython/itsagramlive"

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    dependencies = f.read().splitlines()

setuptools.setup(
    name='ItsAGramLive',
    version='1.2.2',
    packages=setuptools.find_packages(),
    url='https://github.com/harrypython/itsagramlive',
    license='GPL-3.0',
    author='Harry Python',
    author_email='harrypython@protonmail.com',
    description='Its A Gram Live is a Python script that create a Instagram Live and provide you a rtmp server '
                'and stream key to streaming using sofwares like OBS-Studio.',
    project_urls={
        "Example": (project_homepage + "/blob/master/live_broadcast.py"),
        "Bug Reports": (project_homepage + "/issues"),
        "Buy me a coffee": "https://www.buymeacoffee.com/harrypython",
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
    install_requires=dependencies,
)
