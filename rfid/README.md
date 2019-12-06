Build
=====
There are two utilities involved, in order to communicate the rfid tags
via websocket to another application:
1. `getuid` waits for a newline on its standard input and will then try
   to get a token from an mifare-tag by utilising libfreefare and libnfc.
   As soon as a (valid) token has been detected the token-uid is printed
   on stdout.
2. `websocketd.go` is the relay between the web-application and the `getuid`
   utility. It will listen for websocket connections on `ws://localhost:8000`
   and starts a subprocess (executing `argv1 [argv2...]`). Each connection
   may request a token sending `version 1.0` via the websocket. If no other
   request is pending, an empty line is written to stdin of the subprocess,
   to request a new token. As soon as a line is emited by the subprogram on
   stdout, all currently pending websockets will get notified with this token.

The `getuid` program can be (cross) compiled by utilising the `Makefile`. It
is required to have at least the headers of `libnfc` and `libfreefare` available
on the build system. You probably want to build the `release` target. Eventually
you will have either `bin/$ARCH/release` or `bin/$ARCH/debug`.

For `websocketd.go` you need the `nhooyr.io/websocket` package. In order to
cross-compile for the raspberry, you may use the following command:
- `GOARM=7 GOARCH=arm go build src/websocketd.go`

You may use the provided `websocketd@.service` file to ensure the programms are
executed on system boot. Of course, you may have to adjust your paths.

NOTE: `websocketd.go` will also execute `xset dpmfs force on` whenever a new
line is read from its subprogramms stdout.

Install
=======
- Move `websocketd` in a directory of your `$PATH`
- Move `/bin/${ARCH}/release` in a directory of your `$PATH`
- Move `websocketd@.service` to `/etc/systemd/system/`
- `systemctl enable websocketd@getuid`

You may of course adjust `websocketd@.service` if you do not want to have
`websocketd` or `getuid` in your `$PATH`.

Dependencies
============
- [libnfc](https://github.com/nfc-tools/libnfc/)
- [libfreefare](https://github.com/nfc-tools/libfreefare/)

libnfc
------
As of late 2019, the libnfc does not work with modern ACR122 devices, as those
do not allow to set an alternate usb interface. If any of the nfc-tools fail,
have a look into the Troubleshooting section and build your own version:
- `git clone https://github.com/nfc-tools/libnfc`
- `cd libnfc`
- `autoreconf -is`
- `./configure --with-drivers=acr122_usb`
  + (if you do not want to install to `/usr/{bin,lib}` you can use `--prefix=<path>`)
  + (in order to target the raspberry 3B+ use `--host=armv7a-unknown-linux-gnueabihf`)
- `make`
- `sudo make install`

For the currently used rapsberry 3B+ with a 32bit rapsbian, a
`armv7a-unknown-linux-gnueabihf` is required for cross-compilation.

You may use the `nfc-list` or `nfc-scan-device` tools for `libnfc-bin` to ensure
your library is working with the attached nfc reader.

libfreefare
-----------
No issues are known with the upstream version of this library. Therefore, you
should be able to use the version packages by your distribution of choice.
If you need to compile it yourself, those commands should provide you with an
working `libfreefare` (if your `libnfc` is installed to an non standard
location, e.g. you used `--prefix=<path>`, ensure you set
`PKG_CONFIG_PATH=<path>/lib/pkgconfig` and `LD_RUN_PATH=<path>/lib`)
- `git clone https://github.com/nfc-tools/libfreefare`
- `cd libfreefare`
- `autoreconf -is`
- `./configure`
  + (if you do not want to install to `/usr/{bin,lib}` you can use `--prefix=<path>`)
  + (in order to target the raspberry 3B+ use `--host=armv7a-unknown-linux-gnueabihf`)
- `make`
- `sudo make install`

Troubleshooting
===============

Can not open usb device
-----------------------
The recent `libnfc-bin` package should already provide a `udev` rule for all of the
supported drivers. If not, ensure the user is allowed to access the nfc reader:
- `SUBSYSTEMS=="usb" ATTRS{idVendor}=="????" ATTRS{idProduct}=="????" MODE:="0660" GROUP="??"`

Missing symbols `rpl_malloc` and `rpl_realloc` (cross-compile `libfreefare`)
---------------------------------------------------------------------------
If you have to cross-compile `libfreefare` you may encounter missing definitions
of the `rpl_malloc` and `rpl_realloc` functions. This is a known problem and can
be circumvented by applying h `libfreefare-native-alloc.patch`.


Unable to set alternate setting on USB interface (Connection timed out)
-----------------------------------------------------------------------
According to [PR#561](https://github.com/nfc-tools/libnfc/pull/561) the
alternate setting of the USB interface is not available on newer ACR122
NFC readers and might be not required at all on the old ones. Compiling
a modified version of `libnfc` with that PR eventually fixed this issue
for the test systems.

Invalid RDR_to_PC_DataBlock frame
---------------------------------
This error is not as severe as the previous one as the NFC reader emits
still UIDs as soon as some are detected. However, as this will spam the
stderr log with messages and let you eventually overlook a real failure
it should be fixed. I do not know enough about the NFC communication in
libnfc, but [Issue 570](https://github.com/nfc-tools/libnfc/issues/570)
and [Issue 284](https://github.com/nfc-tools/libnfc/issues/284) provide
more information and might help understanding the issue. The referenced
[patch](https://gist.github.com/danieloneill/3be43d5374c80d89ea73) from
the discussion on the first issue removed the error message without any
other problems.
