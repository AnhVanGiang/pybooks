### Install
$ pip install pybooks

## Usage

from pybooks.main import Pbooks \

pbook = Pbooks(file_name='sources.json', \
                author='jerome',\
                title='elements of statistic',\
                weights=(9, 1)) 

pbook.main()
