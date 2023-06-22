```
# [ win + w ] modify gnome screenshot caption
# 2023-06-04 09:54 - AutoKey

clipboard.fill_clipboard("")
time.sleep(0.1)

paste_ = "<ctrl>+v"
time.sleep(0.1)

# example = "Screenshot from 2023-05-14 17-59-48" 
text_ = clipboard.get_selection()
time.sleep(0.1)

# replace unwanted chars in string 
text_ = text_.replace("-","") 
text_ = text_.replace(" ","_")
time.sleep(0.1)
# result = Screenshot_from_20230514_175948

# leftlen_ = 18 
# lefttext_ = "Screenshot_from_20"
lefttext_ = text_[:18] #left length
time.sleep(0.1)

# midlen_ = 6 
# midtext_ = "230514" year
# midtext_ = text_[::6:] #mid length
time.sleep(0.1)

# rightlen_ = 13
# righttext_ = "230514_175948" 
righttext_ = text_[-13:] #right length
time.sleep(0.1)

# 230514_ add underscore
caption_ = (righttext_[:6] + "_")
time.sleep(0.1)

keyboard.send_keys(caption_)
