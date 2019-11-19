/* SPDX-License-Identifier: GPL-3.0-or-later */

/*
 * Simple workaround to auto-fill the password with a random string. Most of
 * our users don't require a password, only admins do.
 *
 * However, Django provides no easy way to handle this. Use this JavaScript
 * instead, thanks to izibi for the idea!
 */

'use strict';

$(document).ready(function() {
    const pw1 = document.getElementById('id_password1');
    const pw2 = document.getElementById('id_password2');
    const err = document.getElementsByClassName('errornote');

    if (pw1 === undefined || pw2 === undefined) {
        return;
    }
    // Don't overwrite any existing password; should never happen as Django
    // resets the password fields
    if (pw1.value !== '' || pw2.value !== '') {
        return;
    }
    // Don't do anything on error, let the user figure out what went wrong;
    // otherwise the user might think the previous password will work after
    if (err.length !== 0) {
        return;
    }

    // 'x' because Django doesn't like entirely numeric passwords
    const pw = 'x' + crypto.getRandomValues(new Uint8Array(40)).join('');
    pw1.value = pw;
    pw2.value = pw;

    console.log("setting random pw", pw);
});
