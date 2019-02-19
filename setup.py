from distutils.core import setup

setup(
    name='pybooks',
    packages=['pybooks'],
    version='0.3',
    license='MIT',
    description='Find a book download URL from multiple online book sources',
    author='Anh Van Giang',
    author_email='vangianganh@gmail.com',
    url='https://github.com/AnhVanGiang/pybooks',
    download_url='https://github.com/AnhVanGiang/pybooks/archive/v_04.tar.gz',
    keywords=['scraper', 'books', 'python'],
    include_package_data=True,
    install_requires=[
        'requests',
        'bs4',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
)
