## Desktop Players

If you use Spotify or any other desktop player App, after restarting **pAudio** you'll need:

- **Restart the desktop player App** in order to reconnect to the new **PipeWire-Jack** instance.
- We also recommend **minimizing Spotify** to prevent the main Spotify window from loading many CPU-intensive widgets, especially on machines with modest CPUs.

All this is done when using **`plugins/spotify_desktop.py`**, Please install the following Debian package before using it:

    apt install xdotool

Then you can add it to `config.yml`

    plugings:
      ...
      ...
      - spotify_desktop.py
  

For other players you can prepare your own plugin by following the same procedure. 
