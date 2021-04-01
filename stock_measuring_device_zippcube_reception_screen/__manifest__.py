# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Stock Zippcube on Reception Screen",
    "summary": "Allow to use the zippcube from a reception screen."
    "for packaging measurement",
    "version": "13.0.1.0.0",
    "category": "Warehouse",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["stock_reception_screen", "stock_measuring_device_zippcube"],
    "data": ["views/stock_reception_screen_view.xml", "views/zippcube_device_view.xml"],
    "website": "https://github.com/OCA/stock-logistics-warehouse",
    "installable": True,
    "development_status": "Alpha",
}
