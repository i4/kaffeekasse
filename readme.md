# Kaffeekasse 2020<sup>NT</sup>

A system for purchasing products and transferring money via a publicly
available terminal. The users are trusted to register all purchases with the
terminal.


## Requirements

* [Django](https://www.djangoproject.com/)
* [PostgreSQL](https://www.postgresql.org/)
* psycopg (PostgreSQL bindings)

* [Bootstrap](https://getbootstrap.com/) for the interface (included)

On a Debian-like system you can install the required packages with
```
apt install python3-django python3-psycopg2 python3-typeguard libjs-jquery
```


### Config

All configurable parameters are stored in `store/store_config.py`.


## Setup

* Create a PostgreSQL database for the current user
* Configure database access via `DATABASES` in `kaffeekasse/settings.py`
* Setup Django with:
```
./manage.py makemigrations
./manage.py migrate
./manage.py createsuperuser

./manage.py runserver
```

Login at http://localhost:8000/admin/ with the super user and start creating
products, categories, users, etc.


## Authors

* Fabian Krüger
* Lukas Schneider
* Simon Ruderich (ruderich@cs.fau.de)


## License

Copyright (C) 2019  Fabian Krüger<br>
Copyright (C) 2019  Lukas Schneider<br>
Copyright (C) 2019  Simon Ruderich<br>

Kaffeekasse 2020NT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
