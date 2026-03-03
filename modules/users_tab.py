import csv
import re

from qtpy import QtWidgets
from modules.adapter import SumoUserAdapter
from modules.tab_base_class import StandardTab
from modules.multithreading import Worker, ProgressDialog
from logzero import logger

class_name = 'UsersTab'

# Maps lowercased/stripped header variants → canonical column name
_HEADER_ALIASES = {
    'firstname':     'firstName',
    'first_name':    'firstName',
    'first name':    'firstName',
    'first':         'firstName',
    'lastname':      'lastName',
    'last_name':     'lastName',
    'last name':     'lastName',
    'last':          'lastName',
    'surname':       'lastName',
    'email':         'email',
    'email_address': 'email',
    'email address': 'email',
    'e-mail':        'email',
    'role':          'role',
    'roles':         'role',
    'role_name':     'role',
}

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_CSV_FIELDS = ['firstName', 'lastName', 'email', 'role']


class UsersTab(StandardTab):

    def __init__(self, mainwindow):
        super(UsersTab, self).__init__(mainwindow)
        self.tab_name = 'Users'
        self.cred_usage = 'both'

        # "Include Roles" checkbox in center column
        self.checkBoxIncludeRoles = QtWidgets.QCheckBox()
        self.checkBoxIncludeRoles.setChecked(True)
        self.checkBoxIncludeRoles.setText("Include\nRoles")
        self.verticalLayoutCenterButton.insertWidget(3, self.checkBoxIncludeRoles)
        self.checkBoxIncludeRoles.show()

        # "CSV ▾" dropdown buttons inserted before the spacer in each bottom button bar
        self.toolButtonCSVLeft = self._make_csv_button('left')
        self.toolButtonCSVRight = self._make_csv_button('right')
        self.horizontalLayoutBottomButtonsLeft.insertWidget(3, self.toolButtonCSVLeft)
        self.horizontalLayoutBottomButtonsRight.insertWidget(3, self.toolButtonCSVRight)

        self.listWidgetLeft.params = {'extension': '.sumouser.json'}
        self.listWidgetRight.params = {'extension': '.sumouser.json'}

        # disconnect the copy signals wired by StandardTab and re-wire with include_roles param
        self.pushButtonCopyLeftToRight.disconnect()
        self.pushButtonCopyRightToLeft.disconnect()

        self.pushButtonCopyLeftToRight.clicked.connect(lambda: self.begin_copy_content(
            self.listWidgetLeft,
            self.listWidgetRight,
            self.left_adapter,
            self.right_adapter,
            {'replace_source_categories': False,
             'include_roles': self.checkBoxIncludeRoles.isChecked()}
        ))

        self.pushButtonCopyRightToLeft.clicked.connect(lambda: self.begin_copy_content(
            self.listWidgetRight,
            self.listWidgetLeft,
            self.right_adapter,
            self.left_adapter,
            {'replace_source_categories': False,
             'include_roles': self.checkBoxIncludeRoles.isChecked()}
        ))

    def _make_csv_button(self, side):
        btn = QtWidgets.QToolButton()
        btn.setText('CSV ▾')
        btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        btn.setFont(self.pushButtonDeleteLeft.font())
        btn.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Fixed
        )
        menu = QtWidgets.QMenu()
        if side == 'left':
            menu.addAction('Export CSV', lambda: self.export_csv_users(
                self.listWidgetLeft, self.left_adapter))
            menu.addAction('Import CSV', lambda: self.import_csv_users(
                self.listWidgetLeft, self.left_adapter))
        else:
            menu.addAction('Export CSV', lambda: self.export_csv_users(
                self.listWidgetRight, self.right_adapter))
            menu.addAction('Import CSV', lambda: self.import_csv_users(
                self.listWidgetRight, self.right_adapter))
        menu.addSeparator()
        menu.addAction('Download Template', self.download_csv_template)
        btn.setMenu(menu)
        return btn

    def reset_stateful_objects(self, side='both'):
        super(UsersTab, self).reset_stateful_objects(side=side)
        if self.left:
            left_creds = self.mainwindow.get_current_creds('left')
            if ':' not in left_creds['service']:
                self.left_adapter = SumoUserAdapter(left_creds, 'left', self.mainwindow)
                self.toolButtonCSVLeft.setEnabled(True)
            else:
                self.toolButtonCSVLeft.setEnabled(False)

        if self.right:
            right_creds = self.mainwindow.get_current_creds('right')
            if ':' not in right_creds['service']:
                self.right_adapter = SumoUserAdapter(right_creds, 'right', self.mainwindow)
                self.toolButtonCSVRight.setEnabled(True)
            else:
                self.toolButtonCSVRight.setEnabled(False)

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def export_csv_users(self, list_widget, adapter):
        if not adapter.is_configured():
            self.mainwindow.errorbox('Please configure credentials before exporting.')
            return

        try:
            users = adapter.sumo.get_users_sync()
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to fetch users:\n\n{e}')
            return

        if not users:
            self.mainwindow.errorbox('No users found.')
            return

        try:
            roles = adapter.sumo.get_roles_sync()
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to fetch roles:\n\n{e}')
            return

        role_id_map = {r['id']: r['name'] for r in roles}

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Export Users to CSV', 'users.csv', 'CSV Files (*.csv);;All Files (*)'
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
                writer.writeheader()
                for user in users:
                    role_names = [role_id_map.get(rid, rid) for rid in user.get('roleIds', [])]
                    writer.writerow({
                        'firstName': user.get('firstName', ''),
                        'lastName':  user.get('lastName', ''),
                        'email':     user.get('email', ''),
                        'role':      '; '.join(role_names),
                    })
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to write CSV:\n\n{e}')
            return

        QtWidgets.QMessageBox.information(
            self, 'Export Complete', f'{len(users)} user(s) exported to:\n{file_path}'
        )

    # ------------------------------------------------------------------
    # CSV template
    # ------------------------------------------------------------------

    def download_csv_template(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save CSV Template', 'users_template.csv', 'CSV Files (*.csv);;All Files (*)'
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
                writer.writeheader()
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to write template:\n\n{e}')
            return

        QtWidgets.QMessageBox.information(
            self, 'Template Saved', f'Template saved to:\n{file_path}'
        )

    # ------------------------------------------------------------------
    # CSV import
    # ------------------------------------------------------------------

    def import_csv_users(self, list_widget, adapter):
        if not adapter.is_configured():
            self.mainwindow.errorbox('Please configure credentials before importing.')
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Import Users from CSV', '', 'CSV Files (*.csv);;All Files (*)'
        )
        if not file_path:
            return

        # utf-8-sig strips the BOM that Excel adds to UTF-8 CSVs
        try:
            with open(file_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                raw_rows = list(reader)
                raw_fieldnames = reader.fieldnames or []
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to read CSV:\n\n{e}')
            return

        # Normalize headers: strip whitespace, lowercase, map aliases → canonical names
        header_map = {}
        for raw in raw_fieldnames:
            canonical = _HEADER_ALIASES.get(raw.strip().lower())
            if canonical:
                header_map[raw] = canonical

        rows = [{header_map.get(k, k): v for k, v in row.items()} for row in raw_rows]
        normalized_fieldnames = {header_map.get(f, f) for f in raw_fieldnames}

        required = {'firstName', 'lastName', 'email', 'role'}
        missing = required - normalized_fieldnames
        if missing:
            self.mainwindow.errorbox(
                f'CSV is missing required column(s): {", ".join(sorted(missing))}\n\n'
                f'Found: {sorted(normalized_fieldnames)}\n\n'
                f'Accepted variants — firstName: first_name, "first name", first | '
                f'lastName: last_name, "last name", surname | '
                f'email: email_address, e-mail | role: roles, role_name'
            )
            return

        if not rows:
            self.mainwindow.errorbox('CSV file contains no data rows.')
            return

        # --- fetch destination roles once ---
        try:
            dest_roles = adapter.sumo.get_roles_sync()
        except Exception as e:
            self.mainwindow.errorbox(f'Failed to fetch roles from target org:\n\n{e}')
            return

        role_map = {r['name'].lower(): r['id'] for r in dest_roles}

        # --- ask user how to handle unrecognized roles ---
        _SKIP = 'Skip rows with unrecognized roles'
        fallback_options = [_SKIP] + sorted(r['name'] for r in dest_roles)
        fallback_choice, ok = QtWidgets.QInputDialog.getItem(
            self, 'Fallback Role',
            'What should happen when a role name from the CSV is not found in this org?',
            fallback_options, 0, False
        )
        if not ok:
            return
        fallback_role_name = None if fallback_choice == _SKIP else fallback_choice
        fallback_role_id = role_map.get(fallback_role_name.lower()) if fallback_role_name else None

        # --- resolve role names → IDs, collect warnings ---
        users_to_create = []
        warnings = []

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            first     = row.get('firstName', '').strip()
            last      = row.get('lastName', '').strip()
            email     = row.get('email', '').strip()
            role_name = row.get('role', '').strip()

            if not (first and last and email):
                warnings.append(f'Row {i}: missing required field(s) — skipping.')
                continue

            if not _EMAIL_RE.match(email):
                warnings.append(f'Row {i} ({email}): invalid email address — skipping.')
                continue

            if role_name.lower() in role_map:
                role_id = role_map[role_name.lower()]
            elif fallback_role_id is not None:
                warnings.append(
                    f'Row {i} ({email}): role "{role_name}" not found — '
                    f'falling back to "{fallback_role_name}".'
                )
                role_id = fallback_role_id
            else:
                warnings.append(
                    f'Row {i} ({email}): role "{role_name}" not found — skipping.'
                )
                continue

            users_to_create.append({
                'firstName': first, 'lastName': last, 'email': email, 'roleId': role_id
            })

        if not users_to_create:
            msg = 'No valid users found in CSV.'
            if warnings:
                msg += '\n\nWarnings:\n' + '\n'.join(warnings)
            self.mainwindow.errorbox(msg)
            return

        # --- confirmation dialog ---
        preview = [f"  {u['firstName']} {u['lastName']} <{u['email']}>" for u in users_to_create]
        confirm_msg = f"{len(users_to_create)} user(s) will be created:\n\n" + '\n'.join(preview[:20])
        if len(preview) > 20:
            confirm_msg += f'\n  … and {len(preview) - 20} more.'
        if warnings:
            confirm_msg += '\n\nWarnings:\n' + '\n'.join(warnings)
        confirm_msg += '\n\nProceed?'

        if QtWidgets.QMessageBox.question(self, 'Confirm User Import', confirm_msg) != QtWidgets.QMessageBox.Yes:
            return

        # --- fire off workers ---
        self._csv_num_threads = len(users_to_create)
        self._csv_completed = 0
        self._csv_successes = 0
        self._csv_failures = []
        self._csv_list_widget = list_widget
        self._csv_adapter = adapter

        self.import_progress = ProgressDialog(
            'Creating users...', 0, self._csv_num_threads,
            self.mainwindow.threadpool, self.mainwindow
        )
        self.workers = []

        for user in users_to_create:
            worker = Worker(
                adapter.sumo.create_user_by_field,
                user['firstName'], user['lastName'], user['email'], [user['roleId']]
            )
            worker.signals.finished.connect(self.import_progress.increment)
            worker.signals.finished.connect(self._csv_on_finished)
            worker.signals.result.connect(self._csv_on_result)
            worker.signals.error.connect(self._csv_on_error)
            self.workers.append(worker)
            self.mainwindow.threadpool.start(worker)

    def _csv_on_result(self, result):
        self._csv_successes += 1

    def _csv_on_error(self, error):
        _exctype, value, _tb = error
        msg = str(value)
        if '409' in msg or 'already exists' in msg.lower() or 'duplicate' in msg.lower():
            msg = f'skipped — email already exists ({msg})'
        self._csv_failures.append(msg)

    def _csv_on_finished(self):
        self._csv_completed += 1
        if self._csv_completed < self._csv_num_threads:
            return
        self.update_item_list(self._csv_list_widget, self._csv_adapter)
        msg = f'{self._csv_successes} user(s) created successfully.'
        if self._csv_failures:
            msg += f'\n\n{len(self._csv_failures)} skipped/failed:\n' + '\n'.join(self._csv_failures)
        QtWidgets.QMessageBox.information(self, 'Import Complete', msg)
