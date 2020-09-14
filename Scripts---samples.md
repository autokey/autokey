See [[Scripting#advanced-scripts]].

- **Author**: Kreezxil
- **Purpose**: Use emoji to write a sentence, for instance on Discord.

```python
retCode, phrase = dialog.input_dialog(title='Give me a phrase',message='to make regional?',default='')

if retCode == 0:
    exit

for x in phrase.lower():
    keyboard.send_keys(" ")
    if x >= 'a' and x <= 'z':
        keyboard.send_keys(':regional_indicator_'+x+':')
    else:
        if x == '*':
            keyboard.send_keys(":asterisk:")
        elif x == '!':
            keyboard.send_keys(":exclamation:")
        elif x == '?':
            keyboard.send_keys(":question:")
        else:
            keyboard.send_keys(x)

``` 