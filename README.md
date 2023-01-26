# SRS Flashcards
Simple flashcard collection based on the Spaced-Repetiton System, using the SM2+ algorithm

## How to use:
0. Clone this repo:

```bash
$ git clone 'https://github.com/nikhilmwarrier/srs-flashcards-system' flashcards && cd flashcards
```

1. Install dependencies
```bash
$ pip install requirements.txt
```

2. Add flashcards to the `new_cards` directory. Flashcards are plain text files containing _only three lines_, in the format:
```
<difficulty_level: integer[0, 10]>
Q: <Question>
A: Answer
```

e.g.  
`creator-of-python.txt` (Make sure that filenames are unique.)  
```
3
Q: Who invented Python?
A: Guido von Rossum
```

3. Run `init.py` with Python
```bash
$ python init.py
```
