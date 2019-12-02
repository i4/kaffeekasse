# SPDX-License-Identifier: GPL-3.0-or-later

"""
N_LAST_BOUGHT_PRODUCTS: number of products to be shown in 'Letzte Einkäufe'
T_ANNULLABLE_PURCHASE_M: time of minutes a user has for a purchase to undo it
N_MOST_BOUGHT_PRODUCTS: number of products to be shown in 'Häufig gekauft'
T_MOST_BOUGHT_PRODUCTS_D: number of days in the past that are used as time intervall limit to search for 'Häufig gekauft'
N_LAST_CHARGES: number of charges that should be shown in 'Letzte Aufladungen'. A negative number means 'all users are
    selected'
T_ANNULLABLE_CHARGE_M: time in minutes a user has for a charge to undo it
N_TRANSFERS_RECEIVERS: number of receivers that should be shown in 'alle Empfänger'. A negative value means 'all
users are shown'
N_LAST_TRANSFERS: number of transfers that should be shown in 'Letzte Überweisungen'
T_ANNULLABLE_TRANSFERS_M: time in minutes a user has for a transfer to undo it
"""
KAFFEEKASSE = {
    'N_LAST_BOUGHT_PRODUCTS': 100,
    'T_ANNULLABLE_PURCHASE_M': 60,
    'N_MOST_BOUGHT_PRODUCTS': 10,
    'T_MOST_BOUGHT_PRODUCTS_D': 30,
    'N_LAST_CHARGES': 10,
    'T_ANNULLABLE_CHARGE_M': 60,
    'N_TRANSFERS_RECEIVERS': -1,
    'N_LAST_TRANSFERS': 10,
    'T_ANNULLABLE_TRANSFERS_M': 60,
}
