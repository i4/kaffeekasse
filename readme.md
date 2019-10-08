# Kaffeekasse 2000<sup>XT</sup>

A system for purchasing products and transferring money based on trust.

## Built with

* [Django](https://www.djangoproject.com/) - The web framework used
* [Bootstrap](https://rometools.github.io/rome/) - The CSS framework used

## Requirements
Additionally to django you need to install the psycopg2 python package:
```
pip install psycopg2
```

## Docs
The project consists of 3 parts. The client, the server and the database.
The client is a simple website.
The server is a web server build with Django for python3.
The server only supports PostgreSQL as database.
For reasons of data integrity, the isolation level serializable is selected.

The models with some simple helper methods can be found in the file store/models.py.
The logic for the backend can be found in store/backend.py.
The http request handlers are located in store/views.py. All exceptions that are passed to the client as error messages are caught here.

### At-Most-Once

At-Most-Once is guaranteed for purchases, money recharching.
The client requests a new token from the server, which it sends together with the actual request. The server checks whether it has already used this token for another request of this type. If so, it aborts and returns success to the client. Otherwise, the request is normally processed.
If anything didn't work, the user sees an error message.
Database transactions that consist of several individual transactions are sent to the database as one transaction and either all or none are executed.

### Config
All configurable parameters are stored in store/store_config.py. See this file for more information.



## Authors

* **Fabian Krueger**
* **Lukas Schneider**

## License

This license covers the project and the logo.<br>
Copyright (C) \<2019\>  \<Fabian Krueger\><br>
Copyright (C) \<2019\>  \<Lukas Schneider\><br>

Kaffeekasse 2000<sup>XT</sup> is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

