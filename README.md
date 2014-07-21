# PISS

<strong>P</strong>ersonal <strong>I</strong>nformation <strong>S</strong>torage and <strong>S</strong>yndication

Increasingly, our digital selves are spread out across a myriad of social networks and there is no central repository of the things that interest you. **PISS** aims to change that. This project borrows many ideas from [IndieWebCamp](http://indiewebcamp.com/) and [Tent](https://tent.io/), but tries not to hold them as dogma.

A public repository of this app can be found here: https://github.com/jenmontes/piss. The [issue tracker](https://github.com/jenmontes/piss/issues) is the preferred channel for bug reports, feature requests, and submitting pull requests.

## PISS? Really?

Yes, really. I feel like using a non-PC name keeps me honest: this project is designed for *my* personal needs and shouldn't cater to anyone else.

## Status

Just ideas at the moment.

## Installation

I really don't recommend trying to install this, but if you insist: all you need to start is a [MongoDB](http://www.mongodb.org/) database. You can get one up and running quickly via `homebrew`. 

Once your database is up and running: 

  1. Clone the PISS repository and `cd` into it
  2. Create a virtual environment with `virtualenv` and activate it
  3. Install the requirements found in `requirements.txt` via `pip`
  4. Start a local PISS server with `python piss.py`
  
Your server should now be available at [http://127.0.0.1:5000](http://127.0.0.1:5000). Running a production instance is out of the scope of this doc, but check out the [Flask](flask.pocoo.org) documentation for more information.

## Acknowledgements

This app owes its existence to the following projects:

* [Flask](http://flask.pocoo.org) by [Armin Ronacher](http://lucumr.pocoo.org/). A micro web development framework for Python.
* [Eve](http://python-eve.org/) by [Nicola Iarocci](http://nicolaiarocci.com/). A REST API framework powered by Flask and MongoDB.

## Authors

* [Jen Montes](https://jenmontes.com) ([Twitter](https://twitter.com/jennifermontes) / [GitHub](https://github.com/jenmontes))

## License
To the extent possible under law, the author has waived all copyright and related or neighboring rights and dedicates this software to the public domain under [CC0](http://creativecommons.org/publicdomain/zero/1.0/).
