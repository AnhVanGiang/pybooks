from setuptools import setup

setup(
    name='pybooks',
    packages=['pybooks'],
    version='1.1',
    license='MIT',
    description='Find a book download URL from multiple online book sources',
    author='Anh Van Giang',
    author_email='vangianganh@gmail.com',
    url='https://github.com/AnhVanGiang/pybooks',
    download_url='https://github.com/AnhVanGiang/pybooks/archive/v_11.tar.gz',
    package_data={'pybooks': ['sources.json']},
    include_package_data=True,
    keywords=['scraper', 'books', 'python'],
    install_requires=[
        'requests',
        'bs4',
        'lxml',
        'sdebugger'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
)
