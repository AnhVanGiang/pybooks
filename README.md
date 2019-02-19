### Install
$ pip install pybooks

## Usage

from pybooks.main import Pbooks \

pbook = Pbooks( author='jerome',\
                title='elements of statistic',\
                weights=(9, 1)) 

pbook.main()

### You can modify or add additional sources by editing the file pybooks/sources.json and follow the current format within the file.
