# MacOS pAudio startup on session init

The install script will place the folowing files for your session init:

    ~/Library/LaunchAgents/com.pAudio.camilladsp.plist
    ~/Library/LaunchAgents/com.pAudio.ctrl.plist
    ~/Library/LaunchAgents/com.pAudio.www.plist

Then, you just need to open a web browser then go to http://localhost:8088 and click there the [ON/OFF] button.

The web page will send the proper command to the **pAudio** **ctrl** daemon in order to lauch the pAudio stuff.
