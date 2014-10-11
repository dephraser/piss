# PISS Themes

Themes should be organized in the following structure:

```
themes
├── theme_name
│   ├── static
│   │   ├── css 
│   │   │   └── style.css
│   │   ├── js
│   │   ...
│   ├── templates
│   │   ├── error.html
│   │   ├── home.html
│   │   ├── post.html
│   │   ...
├── another_theme
...
```

Set the `THEME` variable in `piss.cfg` to the name of your theme to override the default PISS theme. 

You do not need to override all of the files in the default theme! Include only the files you want to modify and the default theme files will be used for the rest.