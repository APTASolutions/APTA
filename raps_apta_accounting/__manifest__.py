# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Apta Accounting Charge",
    'summary': 'Module to provide a way to charge Account Moves',
    'author': "Rapsodoo Iberia",
    'website': "https://www.rapsodoo.com/es/",
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'version': '16.0.1.0.0',

    'depends': [
        'base',
        'account_accountant'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml'
    ],
    'application': False,
}
