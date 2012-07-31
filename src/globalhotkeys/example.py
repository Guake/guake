"""
Copyright (C) 2007 Lincoln de Sousa <lincoln@archlinux-br.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

"""
Globahotkeys test file
======================

Intro
~~~~~
This is a really simple test of globalhotkeys module.

To use this you must compile globalhotkeys module, and run this file with
python. Please only remember to copy your globalhotkeys.so file to a path
contained in sys.path (maybe you can use PYTHONPATH).

The module contains only 3 functions, init/bind/unbind and they are very simple
to use.

What you can not forget?
~~~~~~~~~~~~~~~~~~~~~~~~
 - Compile your module with debug flag, it will help you find a possible
   problem.

 - Run every test from a terminal, all messages will be displayed there.

 - Globalhotkeys module depends on gtk, so if you don't import gtk before call
   any funcion in that module, you will see some warnings on your terminal =D

 - globalhotkeys.init MUST be called before binding/unbinding keys.


What shoud happen here?
~~~~~~~~~~~~~~~~~~~~~~~
This script is a simple test that initializes globalhotkeys machinery and
bindings a key to a simple function. So after running this program, you shoud
se a message 'great =D' or 'bad =('. If every thing goes right, when you press
the F12 key, you should see ('F12',) on your terminal otherwise, you will see a
warning saying that binding has failed.

A really important thing is that globalhotkeys.bind returns boolean values, so
if you want to know if binding works properly, only test this with a simple if.

A cool test
~~~~~~~~~~~
if you want to test your program when it shoud say to the user that the binding
failed, you can simply use this program to bind the key that you're running.
Because you can bind a key once.
"""
import gtk
import globalhotkeys

def hammer(*args):
    print args

globalhotkeys.init()
binded = globalhotkeys.bind('F12', hammer)
if binded:
    print 'great =D'
else:
    print 'bad =('

gtk.main()
