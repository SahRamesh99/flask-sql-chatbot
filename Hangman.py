# Hangman Game

import random
from HangmanWords import Hangmanwords,logo,Stages

lives=6
print(logo)
chosen_word=random.choice(Hangmanwords)
#print(chosen_word)

placehorder=""
word_length=len(chosen_word)
for position in range(word_length):
    placehorder+="_"
print("Word to guess:"+placehorder)

game_over=False
correct_letters=[]

while not game_over:
    print(f"*****************{lives}/6 LIVES LEFT**********************")
    guess=input("Guess a letter:").lower()

    if guess in correct_letters:
        print(f"You've already guessed: {guess}")

    display=""

    for letter in chosen_word:
        if letter==guess:
            display+=letter
            correct_letters.append(guess)
        elif letter in correct_letters:
            display+=letter
        else:
            display+="_"
    
    print("Word to guess:"+display)

    if guess not in chosen_word:
        lives-=1
        print(f"You guessed {guess}, that's not in the word. You lose a life")

        if lives==0:
            game_over=True

            print(f"*****************IT WAS {chosen_word}! YOU LOSE******************")

    if "_" not in display:
        game_over=True
        print("*****************YOU WIN*******************")

    print(Stages[lives])

