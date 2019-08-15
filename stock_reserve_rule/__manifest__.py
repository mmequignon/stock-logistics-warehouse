# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Stock Reservation Rules',
    'summary': 'Configure reservation rules by location zones',
    'version': '12.0.1.0.0',
    'author': "Camptocamp, Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/stock-logistics-warehouse",
    'category': 'Stock Management',
    'depends': [
        'stock_location_zone',
    ],
    'data': [
        'views/stock_reserve_rule_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
