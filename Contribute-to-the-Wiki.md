## Introduction
Anyone with a [GitHub](https://github.com/) account is welcome to contribute to the [AutoKey wiki](https://github.com/autokey/autokey/wiki). A GUI editor is provided and the [Markdown format](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) is used to format the text. Some common wiki-editing procedures are below.

***

## Table of Contents
* [Create a page](#create-a-page)
  * [Put a Table of Contents into your page](#put-a-table-of-contents-into-your-page)
    * [Example Table of Contents](#example-table-of-contents)
* [Edit a page](#edit-a-page)
* [Edit the Table of Contents on the main wiki page](#edit-the-table-of-contents-on-the-main-wiki-page)
* [Find a page](#find-a-page)
* [Rename a page](#rename-a-page)
* [Search this wiki](#search-this-wiki)
* [See also](#see-also)

***

## Create a page
1. Log in to [GitHub](https://github.com/).
2. Visit the [main wiki URL](https://github.com/autokey/autokey/wiki).
3. Check the **Table of Contents** on the right side to see if the page you want to create already exists.
4. If it does, edit that page. Otherwise, click the **"New page"** button in the upper right corner of the page (note that this button is available on all the wiki pages).
5. Type a title into the **"Title"** text-box at the top of the page.
6. Create your page in the editing pane, using [Markdown](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) syntax.
7. Left-click the **"Preview"** tab at any time to see how your changes will look, and left-click the **"Write"** tab to return to the editing pane.
8. When you're satisfied with your change(s), write an **"Edit message"** in the little text-box beneath the editing pane.
9. Click the **"Save page"** button.
10. Copy the link of the page from the URL bar of the browser.
11. Edit the **Table of Contents** on the main wiki page and add the new page's name and URL to the appropriate section of the listing by using the same format as the existing listed	entries.
12. Put an announcement about the new page into [the AutoKey Gitter chat room](https://gitter.im/autokey/autokey) so that others can find it.

### Put a Table of Contents into your page
1. Put a level 2 heading for the Table of Contents wherever you'd like it to be:
```python
## Table of Contents
```
2. Follow that with a list of all the headings in your page by putting an asterisk and a space in front of each one.
```python
## Table of Contents
* Example 1
* Example 2
* Example 3
```
3. Turn each one into a link that doesn't yet point to anywhere by surrounding it in square brackets followed by opening and closing parentheses:
```python
## Table of Contents
* [Example 1]()
* [Example 2]()
* [Example 3]()
```
4. Copy each heading into its empty parentheses to create links that won't yet work:
```python
## Table of Contents
* [Example 1](Example 1)
* [Example 2](Example 2)
* [Example 3](Example 3)
```
5. Make the links inside the parentheses work by:
    1. removing all characters that are not letters, numbers, or dashes
    2. making all letters lower-case
    3. adding a dash between each word
    4. inserting a hash-mark at the beginning
```python
## Table of Contents
* [Example 1](#example-1)
* [Example 2](#example-2)
* [Example 3](#example-3)
```
#### Example Table of Contents
Below is an example with a Table of Contents followed by the headings that it links to:
```python
## Table of Contents
* [Example1](#example1)
* [Example 2](#example-2)
* [Example-3](#example-3)
* [Example 4!!!](#example-4)
* [Example 5: Date in the YYYY.MM.DD HH:MM:SS format](#example-5-date-in-the-yyyymmdd-hhmmss-format)
* [Example 6](#example-6)

## Example1
## Example 2
## Example-3
## Example 4!!!
## Example 5: Date in the YYYY.MM.DD HH:MM:SS format
## [Example 6](https://www.example.com)
```

## Edit a page
1. Log in to [GitHub](https://github.com/).
2. Visit the URL of the page you'd like to edit or open the main wiki page and click on the page you'd like to edit in the **Table of Contents**.
3. Click the **"Edit"** button in the top right corner of the page.
4. Select all of the contents in the editing pane and save them to a text file as a backup and/or reference to use while you're working.
5. Make the change(s) to the page, either by using the same format as the content that's already there or by making improvements to it.
6. Left-click the **"Preview"** tab at any time to see how your changes will look, and left-click the **"Write"** tab to return to the editing pane.
7. When you're satisfied with your change(s), write a summary of what you changed in the **"Edit message"** text-box beneath the editing pane using present-tense for the message.
8. Left-click the **"Save page"** button.
9. Delete or archive the text file you had created in step 4 above.
10. Optional: Put an announcement about the change(s) into [the AutoKey Gitter chat room](https://gitter.im/autokey/autokey) so that others will know about it.

## Edit the Table of Contents on the main wiki page
1. Log in to [GitHub](https://github.com/).
2. Open the main wiki page.
3. Left-click the little pencil in the upper-right corner of the **Table of Contents** on the right side of the page.
4. Select all of the contents in the editing pane and save them to a text file as a backup and/or reference to use while you're working.
5. Make the changes to the **Table of Contents**, either by using the same format as the content that's already there or by making improvements to it.
6. Left-click the **"Preview"** tab at any time to see how your changes will look and left-click the **"Write"** tab to return to the editing pane.
7. When you're satisfied with your change(s), write a summary of what you changed in the **"Edit message"** text-box beneath the editing pane using present-tense for the message.
8. Left-click the **"Save page"** button.
9. Optional: Put an announcement about the change(s) into [the AutoKey Gitter chat room](https://gitter.im/autokey/autokey) so that others will know about it.
10. Delete or archive the text file you had created in step 4 above.

## Find a page
If a wiki page you'd like to find (perhaps one you recently created) isn't listed in the wiki's **Table of Contents** and you'd like to get its name and/or the link to it, you can click the **Pages** drop-down above the wiki's **Table of Contents** and look through all the pages of the wiki to find it.

## Rename a page
1. **Important:** Before you begin, carefully consider the consequences of changing the name of an existing page. It's possible that doing so will break links to the page. A backlink tool, like [this free one from Ahrefs](https://ahrefs.com/backlink-checker), can help to research those. It might also be a good idea to suggest a name change in [the AutoKey Gitter chat room](https://gitter.im/autokey/autokey) first so that others can weigh in on whether or not the change would be welcome as an improvement. 
2. Log in to [GitHub](https://github.com/).
3. Visit the URL of the page you'd like to edit or open the main wiki page and click on the page you'd like to edit in the **Table of Contents**.
4. Click the **"Edit"** button in the top right corner of the page.
5. Change the name of the page in the **"Title"** text-box at the top of the page above the editing pane (note that there's no **"Title"** label for that text-box).
6. When you're satisfied with your change, write a summary of what you changed in the **"Edit message"** text-box beneath the editing pane using present-tense for the message.
7. Left-click the **"Save page"** button.
8. Follow this up by editing the **Table of Contents** on the main wiki page and replacing the name and link with the new ones.
9. Put an announcement about the change(s) into [the AutoKey Gitter chat room](https://gitter.im/autokey/autokey) so that others will know about it.

## Search this wiki
Use the text box in the upper-left corner of the [https://github.com/autokey/autokey/search?type=wikis](https://github.com/autokey/autokey/search?type=wikis) page to search this wiki.

## See also
* See also the [Contributing Code](https://github.com/autokey/autokey/wiki/Contributing-code) page for contributing code to the AutoKey project.
