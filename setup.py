from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='pybooks',
    packages=['pybooks'],
    version='1.4.3',
    license='MIT',
    description='Find a book download URL from multiple online book sources',
    author='Anh Van Giang',
    author_email='vangianganh@gmail.com',
    url='https://github.com/AnhVanGiang/pybooks',
    long_description=long_description,
    long_description_content_type="text/markdown",
    download_url='https://github.com/AnhVanGiang/pybooks/archive/v_15.tar.gz',
    package_data={'pybooks': ['sources.json', 'pbook.exe']},
    include_package_data=True,
    keywords=['scraper', 'books', 'python'],
    install_requires=[
        'requests',
        'bs4',
        'lxml',
        'sdebugger'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
