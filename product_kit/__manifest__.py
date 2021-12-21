# -*- coding: utf-8 -*-
{
    'name': "product_kit",

    'summary': """
        Product Kits""",

    'description': """
        Manage products as kits.
    """,

    'author': "Sahara",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'sale', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/forms/product_product.xml',
        'views/forms/sale_order.xml',
        'views/forms/product_template.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
