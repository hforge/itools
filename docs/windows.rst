How to build itools from Linux to Windows
#########################################

.. highlight:: sh

.. warning::

   This does not work today because the required version of pygobject (2.16
   or later) cannot be installed on Windows.

   See http://bugzilla.gnome.org/show_bug.cgi?id=562790


#. Install Wine

#. | Install MinGW
   | http://sf.net/project/showfiles.php?group_id=2435

   ::

   $ wine MinGW-5.1.4.exe

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

#. | Install GLib and pkg-config
   | http://ftp.acc.umu.se/pub/gnome/binaries/win32/

   ::

   $ cd ~/.wine/drive_c/MinGW/
   $ unzip ~/Downloads/glib_2.20.4-1_win32.zip
   $ unzip ~/Downloads/glib-dev_2.20.4-1_win32.zip
   $ unzip ~/Downloads/pkg-config-0.23-2.zip

#. | Install Python (in Wine)
   | http://www.python.org/download/

   ::

   $ msiexec /i python-2.6.2.msi

#. Edit the file :file:`~/.wine/drive_c/Python26/Lib/distutils/distutils.cfg`

   .. code-block:: none

      [build]
      compiler = mingw32

#. | Install pywin32
   | https://sourceforge.net/projects/pywin32/

   ::

   $ wine pywin32-214.win32-py2.6.exe

#. | Install pygobject
   | http://ftp.gnome.org/pub/GNOME/sources/pygobject/

   .. warning::

      This does not work!

      See http://bugzilla.gnome.org/show_bug.cgi?id=562790

#. Enjoy
   ::

   $ wine c:/Python26/python.exe setup.py bdist_wininst

