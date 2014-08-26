# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from urllib import urlencode
from urlparse import urljoin
from openerp.osv import fields, orm


class mgmtsystem_action(orm.Model):
    _name = "mgmtsystem.action"
    _description = "Action"
    _inherit = "crm.claim"
    _columns = {
        'reference': fields.char('Reference', size=64, required=True, readonly=True),
        'type_action': fields.selection([('immediate', 'Immediate Action'),
                                         ('correction', 'Corrective Action'),
                                         ('prevention', 'Preventive Action'),
                                         ('improvement', 'Improvement Opportunity')],
                                        'Response Type'),
        'system_id': fields.many2one('mgmtsystem.system', 'System'),
        'company_id': fields.many2one('res.company', 'Company'),
        'is_closed': fields.function(
                lambda s, *a, **k : s._func_is_closed(*a, **k),
                type='boolean',
                string='Is closed',
                method=True,
        ),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'reference': 'NEW',
    }

    def create(self, cr, uid, vals, context=None):
        vals.update({
            'reference': self.pool.get('ir.sequence').get(cr, uid, 'mgmtsystem.action')
        }, context=context)
        return super(mgmtsystem_action, self).create(cr, uid, vals, context=context)

    def message_auto_subscribe(self, cr, uid, ids, updated_fields, context=None, values=None):
        """Automatically add the responsible user to the follow list."""
        for o in self.browse(cr, uid, ids, context=context):
            self.message_subscribe_users(cr, uid, ids, user_ids=[o.user_id.id], subtype_ids=None, context=context)
        return super(mgmtsystem_action, self).message_auto_subscribe(cr, uid, ids, updated_fields, context=context, values=values)

    def case_close(self, cr, uid, ids, context=None):
        """When Action is closed, post a message on the related NC's chatter"""
        for o in self.browse(cr, uid, ids, context=context):
            for nc in o.nonconformity_ids:
                nc.case_send_note(_('Action "%s" was closed.' % o.name))
        return super(mgmtsystem_action, self).case_close(cr, uid, ids, context=context)

    def get_action_url(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        action = self.browse(cr, uid, ids[0], context=context)
        base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url', default='http://localhost:8069', context=context)
        query = {'db': cr.dbname}
        fragment = {'id': action.id, 'model': self._name}
        return urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))

    def is_closed_calculation(self, cr, uid, obj, context=None):
        """Is the passed mgmtsystem.action considered to be 'closed'?

        Override this method if you want to change the criteria.

        obj: An mgmtsystem.action object : osv.browse

        Returns: bool
        """
        return obj.stage_id.name in {'Rejected', 'Settled'}

    def is_closed_search(self, cr, uid, context=None):
        """Return the search that finds closed actions in the True case.
        """
        return [('stage_id.name', 'in', ['Rejected', 'Settled'])]

    def _func_search_is_closed(self, cr, uid, model, field_name, query, context=None):
        if field_name != 'is_closed':
            return []

    def _func_is_closed(self, cr, uid, ids, field_name, arg, context=None):
        actions = self.browse(cr, uid, ids, context=context)
        return {
            act.id: self.is_closed_calculation(cr, uid, act, context=context)
            for act in actions
        }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
