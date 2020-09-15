See [[Scripting#advanced-scripts]].

- **Author**: Kreezxil
- **Purpose**: Use emoji to write a sentence, for instance on Discord.
- **Notes**: removed the comment and the if statements, decided to go 100% dictionary lookup method. It is certainly cleaner to look up. It feels a bit faster too.

```python
retCode, phrase = dialog.input_dialog(title='Give me a phrase',message='to make regional?',default='')
lPhrase = phrase.lower()

dictionary = {
    "a":":regional_indicator_a:",
    "b":":regional_indicator_b:",
    "c":":regional_indicator_c:",
    "d":":regional_indicator_d:",
    "e":":regional_indicator_e:",
    "f":":regional_indicator_f:",
    "g":":regional_indicator_g:",
    "h":":regional_indicator_h:",
    "i":":regional_indicator_i:",
    "j":":regional_indicator_j:",
    "k":":regional_indicator_k:",
    "l":":regional_indicator_l:",
    "m":":regional_indicator_m:",
    "n":":regional_indicator_n:",
    "o":":regional_indicator_o:",
    "p":":regional_indicator_p:",
    "q":":regional_indicator_q:",
    "r":":regional_indicator_r:",
    "s":":regional_indicator_s:",
    "t":":regional_indicator_t:",
    "u":":regional_indicator_u:",
    "v":":regional_indicator_v:",
    "w":":regional_indicator_w:",
    "x":":regional_indicator_x:",
    "y":":regional_indicator_y:",
    "z":":regional_indicator_z:",
    "0":":zero:",
    "1":":one:",
    "2":":two:",
    "3":":three:",
    "4":":four:",
    "5":":five:",
    "6":":six:",
    "7":":seven:",
    "8":":eight:",
    "9":":nine:",
    "*":":asterisk:",
    "!":":exclamation:",
    "?":":question:",
    "#":":hash:",
    ".":":small_blue_diamond:"
}

if retCode == 0:
    exit

for x in lPhrase:
    if  x in dictionary:
        keyboard.send_keys(dictionary[x])
    else:
        keyboard.send_keys(x)
    keyboard.send_keys(" ")

``` 