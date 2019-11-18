# Kaffeekasse 2000<sup>XT</sup>

A system for purchasing products and transferring money via a publicly
available terminal. The users are trusted to register all purchases with the
terminal.


## Requirements

* [Django](https://www.djangoproject.com/)
* [PostgreSQL](https://www.postgresql.org/)
* psycopg (PostgrSQL bindings)

* [Bootstrap](https://getbootstrap.com/) for the interface (included)

On a Debian-like system you can install the required packages with
```
apt install python3-django python3-psycopg2
```


## Setup

```
./manage.py makemigratations
./manage.py migrate
./manage.py createsuperuser
```


### Config

All configurable parameters are stored in `store/store_config.py`.


## Authors

* Fabian Krueger
* Lukas Schneider
* Simon Ruderich (ruderich@cs.fau.de)


## License

This license covers the project and the logo.<br>
Copyright (C) 2019  Fabian Krueger<br>
Copyright (C) 2019  Lukas Schneider<br>
Copyright (C) 2019  Simon Ruderich<br>

Kaffeekasse 2000XT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
