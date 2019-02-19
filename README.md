### Install
$ pip install pybooks

## Usage

Simple usage

```from pybooks.main import Pbooks \

pbook = Pbooks( author='jerome',\
                   title='elements of statistic',\
                   weights=(9, 1)) 
         

pbook.main()
```

The ```weights``` argument is used to calculate the accuracy of all the items found and the final chosen url. For example, a ```weights``` of ```(9, 1)``` will place more important on the author accuracy than title's hence it is more likely that the result will have author's name more similar to the input. Default weights are ```(1, 1)```

Optional arguments are ```show_result: Print the result at the end or not```, ```threshold: Only print result with accuracy higher than threshold``` and ```log: Show process while running or not```

### You can modify or add additional sources by editing the file pybooks/sources.json and follow the existing format within the file.

### LICENSE

MIT
