from distutils.core import setup

setup(
    name='pybooks',
    packages=['pybooks'],
    version='0.1',
    license='MIT',
    description='Find a book download URL from multiple online book sources',
    author='Anh Van Giang',
    author_email='vangianganh@gmail.com',
    url='https://github.com/AnhVanGiang/pybooks',
    download_url='https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords=['scraper', 'books', 'python'],
    install_requires=[
        'requests',
        'bs4',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
