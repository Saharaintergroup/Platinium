# -*- coding: utf-8 -*-

{
    "name": "Multi Currency POS",
    "author": "Edge Technologies",
    'version': '17.0.1.0.4',
    "live_test_url": 'https://youtu.be/vJbpPbuiYbo',
    "images": ["static/description/main_screenshot.png"],
    'summary': 'POS check pos check information on POS Cheque Information on point of sale cheque details point of sale check print Cheque Information on the Receipt in POS print cheque number on pos receipt check info pos receipt cheque info pos payment with cheque info',
    "description": """ This app use to print the cheque information on the receipt..

     """,
    "license": "OPL-1",
    "depends": ['base', 'point_of_sale', 'pos_hr', 'account'],
    "data": [
        'secuirty/ir.model.access.csv',
        'secuirty/groups.xml',
        'views/custom_js_added.xml',
        'views/pos_config_inherit.xml',
        'views/payment_provider.xml',
        'views/payment_terminal.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
    "auto_install": False,
    "installable": True,
    "price": 15,
    "currency": 'EUR',
    "category": "Point of Sale",

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
