# SPDX-License-Identifier: GPL-3.0-or-later

# Number of products to be shown in 'Letzte Einkäufe'
N_LAST_BOUGHT_PRODUCTS = 100
# number of products to be shown in 'Häufig gekauft'
N_MOST_BOUGHT_PRODUCTS = 10
# Number of days in the past that are used as time intervall limit to search
# for 'Häufig gekauft'
T_MOST_BOUGHT_PRODUCTS_D = 30

# Show charge link and permit users making their own charges
CHARGE_PERMIT_MANUAL = True
# Number of charges that should be shown in 'Letzte Aufladungen'. A negative
# number means 'all users are selected'
N_LAST_CHARGES = 10

# Time of minutes a user has for a purchase to undo it
T_ANNULLABLE_PURCHASE_M = 60
# Time in minutes a user has for a charge to undo it
T_ANNULLABLE_CHARGE_M = 60
# Time in minutes a user has for a transfer to undo it
T_ANNULLABLE_TRANSFERS_M = 60

# Number of receivers that should be shown in 'alle Empfänger'. A negative
# value means 'all users are shown'
N_TRANSFERS_RECEIVERS = -1
# Number of transfers that should be shown in 'Letzte Überweisungen'
N_LAST_TRANSFERS = 10

# Users cannot purchase products or transfer money if their money gets below
# this amount
MONEY_MIN_LIMIT = 0
