from odoo import models

class MailTemplate(models.Model):
    _inherit = "mail.template"

    def _get_edi_attachments(self, document):
        if not document.sudo().attachment_id or document.edi_format_id.code != 'pe_pse':
            return super()._get_edi_attachments(document)
        return {}