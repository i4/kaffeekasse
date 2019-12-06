#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <signal.h>
#include <ctype.h>
#include <assert.h>
#include <limits.h>

#include <nfc/nfc.h>
#include <freefare.h>

#define ARRAY_SIZE(x)	(sizeof(x)/sizeof(x[0]))
#define debugf(lvl, ...) do { _debugf(lvl, ##__VA_ARGS__, '\n'); } while (false)
#define _debugf_(lvl, fmt, ...) \
	if ((lvl) < (debug_level)) \
		fprintf(stderr, "DEBUG:%02u: " fmt "%c", (lvl), ##__VA_ARGS__)

#ifndef debug_level
# define debug_level	5
#endif

#ifdef NDEBUG
# define _debugf if (false) _debugf_
#else
# define _debugf _debugf_
#endif

struct key {
	uint32_t         app;
	MifareDESFireAID aid;
	MifareDESFireKey key;
	unsigned         kid;
};

struct keyblock {
	uint8_t byte[16];
};

struct config {
	FILE		 *client;
	nfc_context	 *nfc;
	nfc_device	 *dev;
	nfc_connstring    path;
	struct key        key[0
#define KEY(...) +1
#include "keys.h"
	];
};

/*
 * Get the UID of a Mifare Classic, Mifare DESFire without random UID and
 * FAUcard with random UID enabled
 */
static char *
get_tag_uid(struct config *config, FreefareTag tag)
{
	int res;
	char *tag_uid;

	/* Example communication with TAG 04811a4aae2780, wrapped native APDU mode */
	tag_uid = freefare_get_tag_uid(tag);
	debugf(1, "UID:%s NAME:%s", tag_uid,
	       freefare_get_tag_friendly_name(tag));

	/*
	 * This has already happened:
	 *     26
	 * Request type A (ISO14443-3 page 10f)
	 *
	 *     52
	 * Wake-Up (ISO14443-3 page 10f)
	 *
	 * TAG 04  03
	 * ATQA (ISO14443-3 page 13)
	 *
	 *     93  20
	 * Select with cascade level 1 (ISO14443-3 page 16)
	 *
	 * TAG 80  8b  7a  4d  3c
	 * Tag with (random) UID 808b7a4d present
	 */

	if (freefare_get_tag_type(tag) != MIFARE_DESFIRE)
		/* Mifare Classic, UltraLite, ... */
		return tag_uid;
	else if (strlen(tag_uid) > 8)
		/* Mifare DESFire without random UID */
		return tag_uid;
	else if (ARRAY_SIZE(config->key) == 0)
		goto no_uid;

	/*
	 *     93  70  80  8b  7a  4d  3c  e1  40
	 * Select Tag 808b7a4d with cascade level 1 (ISO14443-3 page 16)
	 *
	 * TAG 20  fc  70
	 * SAK
	 *
	 *     e0  50  bc  a5
	 * RATS (ISO14443-4 page 4f, M075040 page 23)
	 *
	 * TAG 06  75  77  81  02  80  02  f0
	 * ATS
	 *
	 */
	debugf(2, "mifare_desfire_connect");
	res = mifare_desfire_connect(tag);
	if (res < 0) {
		debugf(0, "mifare_desfire_connect: %s",
		       freefare_strerror(tag));
		goto no_uid;
	}

	/*
	 * Wrapped native APDU mode begins here: (P1, P2 are always 00), PCB see ISO14443-4 page 14
	 *    PCB CLA INS  P1  P2  Lc  +--Data--+  Le  CRCCRC
	 *     02  90  5a  00  00  03  17  00  00  00  e1  bc
	 * Select application AID 000017 (M075040 page 38)
	 *
	 *    PCB SW1 SW2  CRCCRC
	 * TAG 02  91  00  29  10
	 * OK (Response-code is always SW2: 00)
	 */
	for (unsigned i = 0; i < ARRAY_SIZE(config->key); ++i) {
		const struct key *key = &config->key[i];
		debugf(2, "mifare_desfire_select_application");
		res = mifare_desfire_select_application(tag, key->aid);
		if (res < 0) {
			debugf(2, "select AID:%06x: %s", key->app,
			       freefare_strerror(tag));
			continue;
		}


		/*
		 *     03  90  aa  00  00  01  07  00  26  52
		 * Start AES authentication (AA) on Key number 7 (see libfreefare source)
		 * AES IV is initialized with 00000000000000000000000000000000
		 *
		 *    PCB  +----------------------------Data----------------------------+ SW1 SW2  CRCCRC
		 * TAG 03  aa  be  2f  31  64  a5  f2  36  ad  a3  0a  f4  d6  c4  ec  3f  91  af  eb  66
		 * Tag generates random number RndB (09e78ff5c0ab9c0ce2e2b9e1d44d01e6) and sends it encrypted:
		 * aabe2f3164a5f236ada30af4d6c4ec3f
		 * E(RndB)
		 *
		 *     02  90  af  00  00  20  77  37  91  08  47  1d  6b  e5  ca  6a  62  cf  6f  e9  2c  94  b6  1d  fb  fa  58  14  5c  58  97  4e  c1  73  39  a3  07  0e  00  cb  bf
		 * Host generates 16 byte random RndA (21f86f0492f4baf2184d1f7817938245)
		 * Host decrypts tag random (RndB) and rotates it left one byte (e78ff5c0ab9c0ce2e2b9e1d44d01e609)
		 * Host concatenates both
		 * Host encrypts concatenated 32 bytes with key:
		 * 77379108471d6be5ca6a62cf6fe92c94 b61dfbfa58145c58974ec17339a3070e
		 * E(RndA                         + RndB)
		 *
		 * TAG 02  22  a8  f0  20  d6  07  5b  6b  80  8a  6c  d7  75  06  ba  24  91  00  5c  a3
		 * TAG decrypts both RndA and RndB, compares RndB and if it is correct
		 * TAG rotates RndA left one byte (f86f0492f4baf2184d1f781793824521) and encrypts it:
		 * 22a8f020d6075b6b808a6cd77506ba24
		 * E(RndA)
		 * The resulting session key is:
		 * Ksess = RndA[0..3]+RndB[0..3]+RndA[12..15]+RndB[12..15]
		 *
		 * CMAC subkeys are now calculated with the new session key (see desfire_functions.c)
		 * The AES IV is reset to 00000000000000000000000000000000
		 */
		debugf(2, "mifare_desfire_authenticate_aes");
		res = mifare_desfire_authenticate_aes(tag, key->kid, key->key);
		if (res < 0) {
			debugf(2, "authenticate AID:%06x: %s", key->app,
			       freefare_strerror(tag));
			continue;
		}

		/*
		 *     03  90  51  00  00  00  76  cc
		 * Get card UID (see libfreefare source)
		 *
		 * The CMAC is calculated over the command byte (51) to update the IV (see desfire_functions.c)
		 *
		 * TAG 03  c0  c3  24  02  d6  c8  b9  c1  3f  41  da  d9  3c  36  34  15  91  00  93  ca
		 * Tag responds with encryted uid and crc32(with Ksess):
		 * c0c32402d6c8b9c13f41dad93c363415
		 * decrypted:
		 * Card UID: 04811a4aae2780, CRC32: 2708cd2b
		 */
		debugf(3, "mifare_desfire_get_card_uid (AID:%06x)", key->app);
		res = mifare_desfire_get_card_uid(tag, &tag_uid);
		if (res < 0) {
			debugf(2, "get card uid AID:%06x: %s", key->app,
			       freefare_strerror(tag));
			continue;
		}

		/*
		 *     c2  e0  b4
		 * PCB: S-block DESELECT (ISO14443-4 page 15)
		 *
		 * TAG c2  e0  b4
		 */
		debugf(3, "mifare_desfire_disconnect (AID:%06x)", key->app);
		mifare_desfire_disconnect(tag);
		debugf(1, "AID:%06x: found uid %s", key->app, tag_uid);
		return tag_uid;
	}

no_uid:	free(tag_uid);
	return NULL;
}

static bool
setup_nfc(struct config *config)
{
	nfc_device *dev;

	assert(config->nfc);
	assert(config->dev == NULL);

	debugf(3, "nfc_open(%s)", config->path);
	dev = nfc_open(config->nfc, config->path);
	if (dev == NULL)
		return false;
	/* configure for mifare */

	debugf(3, "nfc_initiator_init");
	nfc_initiator_init(dev);

	// Drop the field for a while
	debugf(3, "set_property(ACTIVATE_FILED, false)");
	nfc_device_set_property_bool(dev, NP_ACTIVATE_FIELD, false);

	// Configure the CRC and Parity settings
	debugf(3, "set_property(HANDLE_CRC, true)");
	nfc_device_set_property_bool(dev, NP_HANDLE_CRC, true);
	debugf(3, "set_property(HANDLE_PARITY, true)");
	nfc_device_set_property_bool(dev, NP_HANDLE_PARITY, true);
	debugf(3, "set_property(AUTO_ISO14443_4, true)");
	nfc_device_set_property_bool(dev, NP_AUTO_ISO14443_4, true);

	// Enable field so more power consuming cards can power themselves up
	debugf(3, "set_property(ACTIVATE_FILED, true)");
	nfc_device_set_property_bool(dev, NP_ACTIVATE_FIELD, true);

	config->dev = dev;
	return true;
}

static bool
reset_nfc(struct config *config)
{
	assert(config->nfc);
	if (config->dev) {
		debugf(0, "reset %s: %s", config->path,
		       nfc_strerror(config->dev));
		nfc_close(config->dev);
	}
	return setup_nfc(config);
}

static const nfc_modulation modulations[] = {
	/* MIFARE */
	{ .nmt = NMT_ISO14443A, .nbr = NBR_106 },
	/* FELICA */
	{ .nmt = NMT_FELICA, .nbr = NBR_424 },
	{ .nmt = NMT_FELICA, .nbr = NBR_212 },
};

static void
request(struct config *config)
{
	/* TODO: nfc_device_get_supported_modulation */
	char *uid = NULL;

	/* setup initator */
	nfc_initiator_init(config->dev);
	while (true) {
		nfc_target target;
		debugf(1, "nfc_initiator_poll_target");
		uint8_t interval = 2 /* unit: 150ms */;
		int err = nfc_initiator_poll_target(config->dev, modulations,
						    ARRAY_SIZE(modulations),
						    0xff, interval, &target);
		if (err == NFC_ETIMEOUT) {
			continue;
		} else if (err <= 0) {
			debugf(0, "nfc_initiator_poll_target: %s [%i|%i]",
			       nfc_strerror(config->dev), err,
			       nfc_device_get_last_error(config->dev));
			if (err == NFC_SUCCESS)
				/* should not happen...? */
				continue;
			else if (err == NFC_EIO)
				continue;

			while (!reset_nfc(config)) {
				debugf(3, "retry reset in 1 second");
				usleep(50UL * 1000);
			}
		} else { /* found a tag */
			/* I do not know why, but a simple `freefare_tag_new`
			 * will not allow a later connect to succeed. Therfore
			 * do not directly use the target returned by
			 * `nfc_initiator_poll_target` but use the libfreefare
			 * provided `freefare_get_tags` function. */
			FreefareTag *tags = freefare_get_tags(config->dev);
			if (tags == NULL)
				continue;

			for (FreefareTag *tag = tags; !uid && *tag; ++tag)
				uid = get_tag_uid(config, *tag);

			freefare_free_tags(tags);
			if (uid)
				break;
		}
		usleep(50UL * 1000);
	}
	debugf(1, "forward token '%s'", uid);
	fprintf(config->client, "%s\n", uid);
	fflush(config->client);
	free(uid);
}

static bool __attribute__((unused))
setup_key(struct key *key, uint32_t aid, unsigned kid,
	  const struct keyblock *data)
{
	key->key = mifare_desfire_aes_key_new(data->byte);
	if (key->key == NULL)
		return false;
	key->aid = mifare_desfire_aid_new(aid);
	if (key->aid == NULL)
		return false;
	key->app = aid;
	key->kid = kid;
	return true;
}
#define setup_key(key, aid, kid, ...) \
	setup_key(key, aid, kid, &(const struct keyblock){.byte={__VA_ARGS__}})

int
main(int argc, char *argv[])
{
	// Ignore SIGPIPE
	struct sigaction action = { .sa_handler = SIG_IGN };
	sigemptyset(&action.sa_mask);
	sigaction(SIGPIPE, &action, NULL);

	// Do NFC stuff
	unsigned devices;
	struct config config = {
		.client = stdout,
		.nfc    = NULL,
		.dev    = NULL,
	};

	debugf(3, "nfc_init");
	nfc_init (&config.nfc);
	if (config.nfc == NULL) {
		fprintf(stderr, "Could not init nfc_context\n");
		exit(EXIT_FAILURE);
	}

	debugf(3, "create keys");
	for (unsigned i = 0; i < ARRAY_SIZE(config.key); ++i) {
#define KEY(AID, KID, ...)						\
		if (setup_key(&config.key[i++], AID, KID, __VA_ARGS__))	\
			continue;					\
		fprintf(stderr, "Could not initialize key %u\n", i-1);	\
		exit(EXIT_FAILURE);
#include "keys.h"
	}

	debugf(3, "nfc_list_devices");
	devices = nfc_list_devices(config.nfc, &config.path, 1);
	if (!devices) {
		fprintf(stderr, "No NFC device found\n");
		exit(EXIT_FAILURE);
	}

	if (!setup_nfc(&config)) {
		fprintf(stderr, "could not setup device '%s'\n", config.path);
		exit(EXIT_FAILURE);
	}

	int result;

	/* wait for a client:
	 * libnfc does not provide a mechanism to get notified as soon as a
	 * new token was detected. Therefore, we will not poll libnfc as long
	 * as the client does not issue a request (by writing a newline to our
	 * stdin */
	while ((result = fgetc(stdin)) != EOF) {
		if (result == '\n')
			request(&config);
	}
	result = EXIT_SUCCESS;
	if (!feof(stdin)) {
		perror("could not read from client");
		result = EXIT_FAILURE;
	}
	nfc_close(config.dev);
	return result;
}
