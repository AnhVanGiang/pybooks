### Install
```sh
$ pip install pybooks
```

## Usage

Simple usage

```
from pybooks.pbook import Pbooks 

pbook = Pbooks( author='jerome',
                title='elements of statistic',
                weights=(9, 1)) 
         

pbook.main()
```

The ```weights``` argument is used to calculate the accuracy of all the items found and the final chosen url. For example, a ```weights``` of ```(9, 1)``` will place more important on the author accuracy than title's hence it is more likely that the result will have author's name more similar to the input. Default weights are ```(1, 1)```

Optional arguments are ```show_result: Print the result at the end or not```, ```threshold: Only print result with accuracy higher than threshold``` and ```log: Show process while running or not```, etc. More arguments can be found in the documentation of the code.

### You can modify or add additional sources by editing the file pybooks/sources.json and follow the existing format within the file.

### Sources.json format, rules

Example: 
[Library Genesis with elements of statistics as search term](http://gen.lib.rus.ec/search.php?&req=elements+of+statistics&phrase=1&view=simple&column=def&sort=def&sortmode=ASC&page=1)

The only components we need in the URL are: ```request: ?req=...```, ```delimiter: + (elements+of+statistics)``` and ```pagination: 
page=...``` and ```term_concatenation: & (req=...&page=...)```

```
INSIDE SOURCES.JSON

URL: main url without search terms
URL_RULES: dictionary contains keys and values as search rules.
HTML_RULES: Contains nested dictionary represent necessary components to conduct searches such as tags, attributes for titles, authors, rows and page body
.POSITION: The position of the that element in the row if there are other similar elements with similar tag and attributes, leave as null if it is unique
.TAG: The tag of the desired element
.ATTRIBUTE: Attributes of the tag, for exanple: {"class": "id", "...": "..", ...}. Leave the value of a key as true if an attribute has no value
```
### COMMAND LINE USAGE
You can use the package directly from the command line
Example: Searching a book with title: "Elements of statistical learning" and author: "Jerome Friedman"
You can add pbook.exe to environment variables and use it from the command line by this command with ```%PATH%``` as your path to pybooks directory (folder), usually found in ```\Python{version}\Lib\pybooks```.
```sh
setx PATH "%PATH%
```

```sh
pbook -a "jerome friedman" -t "elements of statistical learning"
```
```sh
OPTIONAL ARGUMENTS
-h, --help            show this help message and exit
  -a AUTHOR, --author AUTHOR
                        Author of the book you want to find
  -t TITLE, --title TITLE
                        Title of the book you want to find
  -w WEIGHTS, --weights WEIGHTS
                        Assign author and title weight to the final accuracy
                        calculation
  -th THRESHOLD, --threshold THRESHOLD
                        Only get results above the threshold amount
  -l LOG, --log LOG     Print out the process
  -s SHOW, --show SHOW  Show result at the end of running
  -br BREAK_AT, --break-at BREAK_AT
                        Stop when encounter a book with accuracy higher than
                        or equal to this number
  -m METHOD, --method METHOD
                        Choose a book evaluation method

```

### LICENSE

MIT
