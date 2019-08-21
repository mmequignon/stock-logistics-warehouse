# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models
from odoo.exceptions import ValidationError


class IrSequenceWizard(models.TransientModel):
    """
    Class for implementation generation of sequence in cases not supported
    default model ir.sequence
    """

    _name = 'ir.sequence.wizard'

    number_next_actual = fields.Char(string='Next Number')

    def _next(self):
        self.ensure_one()
        number_next_actual = self.number_next_actual
        if self.number_next_actual.isdigit():
            self.write(
                {'number_next_actual': str(int(self.number_next_actual) + 1)}
            )
        else:
            raise ValidationError('Only numbers are expectable')
        return number_next_actual
