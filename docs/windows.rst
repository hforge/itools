How to build itools from Linux to Windows
#########################################

.. highlight:: sh

#. Install Wine

#. Install MinGW

   #. | Download the ``mingw-get-inst-20101030.exe`` file from
      | http://sourceforge.net/projects/mingw/files/

   #. Run it ::

      $ wine mingw-get-inst-20101030.exe

#. Add MinGW to the system's path

   #. Launch regedit ::

      $ regedit

   #. Go to:

      .. code-block:: none

           HKEY_LOCAL_MACHINE
             System
               CurrentControlSet
                 Control
                   Session Manager
                     Environment

   #. Append "C:\\MinGW\\bin" to the "PATH" variable

#. | Install GLib, pkg-config, gettext and zlib
   | http://www.gtk.org/download-windows.html

   ::

   $ cd ~/.wine/drive_c/MinGW/
   $ unzip ~/Downloads/glib_2.26.0-2_win32.zip
   $ unzip ~/Downloads/glib-dev_2.26.0-2_win32.zip
   $ unzip ~/Downloads/pkg-config_0.23-3_win32.zip
   $ unzip ~/Downloads/zlib_1.2.5-2_win32.zip
   $ unzip ~/Downloads/gettext-runtime_0.18.1.1-2_win32.zip
   $ cp bin/intl.dll lib/

#. | Install Python (in Wine)
   | http://www.python.org/download/

   ::

   $ msiexec /i python-2.6.6.msi

#. Edit the file :file:`~/.wine/drive_c/Python26/Lib/distutils/distutils.cfg`

   .. code-block:: none

      [build]
      compiler = mingw32

#. | Install pywin32
   | https://sourceforge.net/projects/pywin32/

   ::

   $ wine pywin32-214.win32-py2.6.exe

#. | Install pygobject
   | http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/

   ::

   $ wine pygobject-2.26.0.win32-py2.6.exe

#. Enjoy
   ::

   $ wine c:/Python26/python.exe setup.py bdist_wininst
