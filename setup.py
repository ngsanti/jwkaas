import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='jwkaas',  
     version='0.1',
     scripts=[],
     author="Bernie van Veen",
     author_email="b.vanveen@vwt.digital",
     description="JSON Web Key Advanced Archiving Store",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/vwt-digital/jwkaas",
     packages=setuptools.find_packages(),
     install_requires= [
         'pyjwt==1.7.1',
         'cryptography==2.6.1'
     ],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: GPLv3 License",
         "Operating System :: OS Independent",
     ],
 )
