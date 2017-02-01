# Support for Node-RED Python blocks

This package aims to ease the sometimes tedious development of Node-RED blocks
(also called *nodes*) that are backed by a Python process.

Node-RED allows for rapid development and experimentation using visual
programming and a flow-oriented approach. However out-of-the-box it only allows
Javascript to be used for implementing individual code blocks. Javascript has
relatively poor support for numeric calculations and signal processing. On the
other hand, Python has a large collection of existing libraries for such
purposes, including NumPy, SciPy. Hence, a wish to be able to implement some
parts of Node-RED flows in Python.

This package contains boilerplate code, mostly centered around the `SFNRBaseNode`
Python class and a `sfnr` launcher application. It allows Node-RED block to be
created in pure Python by subclassing the `SFNRBaseNode` class. This creates
both a block in the Node-RED visual editor (installed by `setup.py`) and a
back-end process that can be launched through the `sfnr` command line.

An example block is included that communicates with the Node-RED flow through a
HTTP REST API and returns a *Hello, World!* greeting in form of a JSON object.

## How to install

Run the following in the directory containing `setup.py`:

    $ pip install -U .

This command will install all required Javascript and Python components
automatically.

Note that at the moment, this expects that your Node-RED installation is under
`~/node_modules/node-red`.

After installing, restart Node-RED. An *examples* category of nodes should appear
in the toolbox on the left, containing an *example* node.

## How to use

In the context of the `sigfox-toolbox`, this package has no use on its own.
It's only provided to increase the modularity of the distribution.

If you would like to implement your own Python nodes, see the `example` block
under `sfnr.nodes.example`. Each block should be in its own Python module under
`sfnr.nodes` (which is a Python namespace package).

The module should contain a `SFNRNode` class (a subclass of `SFNRBaseNode`).
You should override at least the following:

 *  `PORT` - port number used for communication between the back-end process
    and the Node-RED flow.
 *  `NAME` - friendly name for the block.
 *  `SLUG` - machine name for the block, used internally in Node-RED. Typically
    alphanumeric, all lower-case.
 *  `DESC` - HTML snippet displayed in the Node-RED editor *info* box.
 *  `CATEGORY` - category under which the block will be visible in the Node-RED
    editor's toolbox.
 *  `work(msg)` - a method that takes a JSON object (payload from incoming
    message) and returns a JSON object (payload for the outgoing message).

By default, the node uses a HTTP REST API interface. If you need some other
interface (e.g. a raw TCP socket), you also need to do the following:

 *  Override `run(opts)` method on `SFNRNode` to setup the custom communication
    channel.
 *  Override `TEMPLATE` property to provide a custom template name.
 *  Provide custom Javascript and HTML templates for the Node-RED blocks under
    the `templates` directory.

An example of a node the uses a custom interface is the `sensor` node in
`node-red-spectrum-sensing`.

## See also

 *  [Node-RED: Creating Nodes](http://nodered.org/docs/creating-nodes/)

## Author and license

Node-RED spectrum sensing blocks were written by Tomaž Šolc, **tomaz.solc@ijs.si**.

Copyright (C) 2017 SensorLab, Jožef Stefan Institute http://sensorlab.ijs.si

Javascript code was adopted from the Node-RED distribution, which is Copyright
2013, 2016 IBM Corp.

The research leading to these results has received funding from the European
Horizon 2020 Programme project eWINE under grant agreement No. 688116.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see http://www.gnu.org/licenses
