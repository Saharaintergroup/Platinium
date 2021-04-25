# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InheritPos(models.Model):
    _inherit = 'pos.session'

    def check_status(self):
        for rec in self:
            rec.write({'state': 'closed','stop_at': rec.start_at})
            return True
