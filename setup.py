import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ItsAGramLive',
    version='0.1.1',
    packages=setuptools.find_packages(),
    url='https://github.com/harrypython/itsagramlive',
    license='GPL-3.0',
    author='Harry Python',
    author_email='harrypython@protonmail.com',
    description='Its A Gram Live is a Python script that create a Instagram Live and provide you a rtmp server and stream key to streaming using sofwares like OBS-Studio.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
)
