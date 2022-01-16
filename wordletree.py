#!/usr/bin/env python3

GUESSES=set()
ANSWERS=set()

with open('guesses.txt', 'r') as f:
    for line in f:
        GUESSES.add(line.lower().strip())
with open('answers.txt', 'r') as f:
    for line in f:
        ANSWERS.add(line.lower().strip())


def posmap(string):
    return {i:string[i] for i in range(len(string))}

def score(guess, against):
    '''Return a tuple of 5 integers representing the score of this word against the list'''
    r = [0] * 5
    guessletters = posmap(guess)
    againstletters = posmap(against)

    for k,v in guessletters.copy().items():
        if v == againstletters[k]:
            r[k] = 2
            del againstletters[k]
            del guessletters[k]

    for k,v in guessletters.items():
        for kb, vb in againstletters.items():
            if v == vb:
                del againstletters[kb]
                r[k] = 1
                break

    return tuple(r)

def main():
    guessmin = {}
    for word in GUESSES:
        wordscores = {}
        for word2 in ANSWERS:
            wordscore = score(word, word2)
            if wordscore in wordscores:
                wordscores[wordscore] += 1
            else:
                wordscores[wordscore] = 1
            print('%s : %s -> %s'% (word, word2, score(word, word2)))
        maxv = max(wordscores.values())
        guessmin[word] = maxv
    minimum = min(guessmin.values())
    for k,v in guessmin.items():
        if v == minimum:
            print('%s is a good choice (score: %d)' % (k, v))


main()

