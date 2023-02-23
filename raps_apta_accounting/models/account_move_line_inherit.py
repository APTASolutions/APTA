# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, _
import xlrd
from datetime import datetime
import logging
import base64
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    comment = fields.Char(
        string='Comment'
    )

    def _first_account_move_charge(self):
        journal_id = self.env['account.journal'].search([('name', '=', 'Asientos 2021-2022')], limit=1)
        req_columns = self.get_columns_names()
        account_move_env = self.env['account.move']
        move_line_env = self.env['account.move.line']
        account_account_env = self.env['account.account']
        account_number = 0
        list_move = []
        list_lines = []
        file = self.env['ir.attachment'].search([('name', 'ilike', 'Apta')], limit=1)
        if file:
            file_content = base64.decodebytes(file.datas)
            wb = xlrd.open_workbook(file_contents=file_content)
            sheet = wb.sheet_by_index(0)
            cols_count = sheet.ncols
            rows_count = sheet.nrows
            for row in range(1, rows_count):
                # Get clean dictionaries
                # For each row mappe all the columns required
                # Save it as a new record in list_move
                account_data = self.get_account_original_data(journal_id.id)
                line_data = self.get_line_original_data()
                for column in range(cols_count):
                    # For each column get the values to create the record
                    if column == (cols_count - 1):
                        # Account record will be created only one
                        # So, if exist an Account record with the same account number will not be created
                        exist_account = [ac for ac in list_move if ac.get('account_number') == account_number]
                        if not exist_account:
                            list_move.append(account_data)
                        line_data.update({'account_number': account_number})
                        list_lines.append(line_data)
                        _logger.info('Row:::{}'.format(str(row)))
                        _logger.info(
                            'Account_data :::: {}'.format(account_data.get('name') + str(account_data.get('journal_id'))))
                        _logger.info('Line_data ::::{}'.format(str(line_data.get('debit')) + str(line_data.get('credit'))))
                    if sheet.cell_value(0, column) in req_columns:
                        # Generate Data for the Account Move
                        first_cell = sheet.cell_value(0, column)
                        if first_cell == 'Fecha':
                            sheet_date = sheet.cell_value(row, column)
                            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(sheet_date) - 2).date()
                            account_data.update({'date': dt})
                        elif first_cell == 'asiento':
                            account_number = sheet.cell_value(row, column)
                            name = 'AST-{}-{}'.format(dt.year, self.get_sequence(int(account_number)))
                            account_data.update({'account_number': account_number})
                            account_data.update({'name': name})
                        elif first_cell == 'Comentario':
                            comment = sheet.cell_value(row, column)
                            line_data.update({'comment': comment})
                        # Generate Data for Account Move Line
                        elif first_cell == 'CodigoCuenta':
                            account = sheet.cell_value(row, column)
                            account_id = account_account_env.search([('code', '=', int(account))], limit=1)
                            line_data.update({'account_id': account_id.id})
                        elif first_cell == 'Debe':
                            debit = sheet.cell_value(row, column)
                            if debit >= 0:
                                line_data.update({'debit': abs(debit)})
                            else:
                                line_data.update({'credit': abs(debit)})
                        elif first_cell == 'Haber':
                            credit = sheet.cell_value(row, column)
                            if credit >= 0 and not line_data.get('credit'):
                                line_data.update({'credit': abs(credit)})
                            else:
                                line_data.update({'debit': abs(credit)})
            for move in list_move:
                account_move = account_move_env.create(self.get_move_data(move))
                move_lines = [ml for ml in list_lines if ml.get('account_number') == move.get('account_number')]
                _logger.info('Account Created ::::' + str(move.get('account_number')))
                _logger.info('Account year ::::' + str(account_move.date.year))
                for line in move_lines:
                    line.update({'move_id': account_move.id})
                    move_line = move_line_env.with_context(check_move_validity=False).create(self.get_line_data(line))
                    _logger.info('Move Created ::::' + str(move_line.id))
                    _logger.info('Move debit ::::' + str(move_line.debit))
                    _logger.info('Move credit ::::' + str(move_line.credit))
            file.unlink()

    @staticmethod
    def get_move_data(move):
        return {
            'date': move.get('date'),
            'name': move.get('name'),
            'journal_id': move.get('journal_id'),
        }

    @staticmethod
    def get_line_data(line):
        return {
            'account_id': line.get('account_id'),
            'debit': line.get('debit'),
            'credit': line.get('credit'),
            'name': line.get('comment'),
            'move_id': line.get('move_id')
        }

    @staticmethod
    def get_line_original_data():
        line_data = {
            'account_number': False,
            'account_id': False,
            'comment': False,
            'debit': False,
            'credit': False,
            'move_id': False
        }
        return line_data

    @staticmethod
    def get_account_original_data(journal_id):
        account_data = {
            'account_number': False,
            'date': False,
            'name': False,
            'journal_id': journal_id,
        }
        return account_data

    @staticmethod
    def get_sequence(account_number):
        length = 5
        return str(account_number).zfill(length)

    @staticmethod
    def floatHourToTime(sheet_date):
        hours, hourSeconds = divmod(sheet_date, 1)
        minutes, seconds = divmod(hourSeconds * 60, 1)
        return (
            int(hours),
            int(minutes),
            int(seconds * 60),
        )

    @staticmethod
    def get_columns_names():
        return ['Fecha', 'asiento', 'Comentario', 'CodigoCuenta', 'Debe', 'Haber']

    def _set_to_posted_accounts(self):
        accounts = self.env['account.move'].search([('state', '!=', 'posted'), ('name', 'ilike', 'AST')])
        for rec in accounts:
            _logger.info('Updating State for account ::::' + str(rec.name))
            rec.state = 'posted'

