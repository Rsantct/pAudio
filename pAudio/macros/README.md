# Macros
This folder is intended for general purpose user macro scripts, for example for automation tasks,
to go to listen to radio presets, etc...

**(i) The control web page will find here macro files:**

Any file here named like **`NN_some_nice_name`** ( `NN` >= `01`) will be consider as an user macro by the control web page, then a web button will be used to trigger the macro.

Files not named this way, will be ignored from the control web page.

NN determines the position into the web macros key pad.

An example:

```
$ ls -1 pAudio/code/macros/
01_RNE
02_R.Clasica
06_flat sound
README.md
```

Will show the following key pad layout:

```
    [     RNE     ]  [  R.Clasica  ]  [     --     ]
    [     --      ]  [     --      ]  [ flat sound ]
```
