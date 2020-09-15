See [[Scripting#advanced-scripts]].

- **Author**: Kreezxil
- **Purpose**: Use emoji to write a sentence, for instance on Discord.

```python
retCode, phrase = dialog.input_dialog(title='Give me a phrase',message='to make regional?',default='')
lPhrase = phrase.lower()

numbers = {
    "0":":zero:",
    "1":":one:",
    "2":":two:",
    "3":":three:",
    "4":":four:",
    "5":":five:",
    "6":":six:",
    "7":":seven:",
    "8":":eight:",
    "9":":nine:"
}
if retCode == 0:
    exit

for x in lPhrase:
    if x >= 'a' and x <= 'z':
        keyboard.send_keys(':regional_indicator_'+x+':')
    elif x in numbers:
        keyboard.send_keys(numbers[x])
    else:
        if x == '*':
            keyboard.send_keys(":asterisk:")
        elif x == '!':
            keyboard.send_keys(":exclamation:")
        elif x == '?':
            keyboard.send_keys(":question:")
        elif x == '#':
            keyboard.send_keys(":hash:")
        elif x == '.':
            keyboard.send_keys(":small_blue_diamond:")
        else:
            keyboard.send_keys(x)
    keyboard.send_keys(" ")
    #time.sleep(0.425)

#optimized region script to store the value of a phrase after its been lowered, seems to parse faster. Also using a number dictionary for processing numbers. Which seems to be faster than 10 Elifs. I might go full dictionary with this. The comment out sleep statement was there as I was testing if Discord had a throttle in place.
``` 