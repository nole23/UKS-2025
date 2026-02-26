import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { UserService } from '../../services/user';
import { ModalDialogComponent } from '../../helpers/modal-dialog-component/modal-dialog-component';
import { finalize } from 'rxjs';
import { AuthService } from '../../services/auth';
import { TableComponent } from '../../helpers/table-component/table-component';
import { TableColumn } from '../../helpers/interface/table-column';

@Component({
  selector: 'app-account-settings',
  imports: [FormsModule, CommonModule, RouterModule, ModalDialogComponent, TableComponent],
  templateUrl: './account-settings.html',
  styleUrl: './account-settings.scss',
})
export class AccountSettings implements OnInit {

  modalTitle: string = '';
  modalMessage: string = '';
  modelType: string = '';
  isRedirect: boolean = false;

  isMessage: boolean = false;

  email: string = '';
  user: any = null;

  account: any = {
    first_name: "",
    last_name: "",
    company_name: "",
    company_email: "",
    company_website: "",
    company_location: ""
  };

  emailUpdate: any = {
    old_email: '',
    new_email: ''
  }

  updatePassword: any = {
    old_password: '',
    new_password: ''
  }

  newEmail = '';
  tokens: any[] = [];
  showTokenForm = false;
  newTokenName = '';
  settingsOpen = true;
  selectedMenu: string = 'accountInfo';

  loading = false;       // spinner flag

  showPasswordModal: boolean = false; // flag za popup
  simulatedEmailContent: string = ''; // sadržaj emaila

  isLoadingToken = false;
  loadData: boolean = true;

  tokenColumns: TableColumn[] = [
    { key: 'name', label: 'Name' },
    { key: 'token', label: 'Token' },
  ];

  roleColumns: TableColumn[] = [
    { key: 'name', label: 'Role Name' },
    { key: 'checked', label: 'Select Role', type: 'radio' }, // Opciono
  ];

  roles: any = [];
  isShowRole: boolean = false;
  isRoleLoader: boolean = false;

  selectRole: string = '';

  constructor(public userService: UserService, private route: ActivatedRoute, private auth: AuthService) {}

  ngOnInit(): void {
    let username = this.route.snapshot.paramMap.get('username');

    this.userService.filterUserByUsername(username ?? '')
      .subscribe({
        next: (res) => {
          this.user = res;
          this.loadData = false

          this.email = this.user.email;
          this.account = { ...this.user, ...this.user.profile };

          this.getRole();
          this.getTokens();
        },
        error: () => {
          this.modalTitle = 'Server unavailable';
          this.modalMessage = 'Server is currently unavailable, please log out and try again in a few moments.';
          this.modelType = 'Error';
          this.isMessage = true;
          this.isRedirect = true;
        }
      });
  }

  private getRole() {
    if (this.userService.isAdminOrSuperadmin()) {
      this.userService.getCurrnetRoles().subscribe({
        next: (res) => {
          this.roles = res.roles.map((role: string) => ({
            name: role,
            checked: this.user.role == role
          }))
        }
      })
    }
  }

  toggleSettings() {
    this.settingsOpen = !this.settingsOpen;
  }

  selectMenu(menu: string) {
    this.selectedMenu = menu;
  }

  selectMenuAndClose(menu: string) {
    this.closeModal();
    this.selectMenu(menu);
  }

  saveAccountInfo() {
    if (!this.hasAccountChanges()) {
      alert('The model has not changed.')
    }

    this.loading = true;  // start spinner

    this.userService.updateProfile(this.account)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: () => {
          this.modalTitle = '';
          this.modalMessage = 'We have successfully completed the update!';
          this.modelType = 'info';
          this.isMessage = true;
        },
        error: () => {
          this.modalTitle = '';
          this.modalMessage = 'An error occurred while updating.';
          this.modelType = 'error';
          this.isMessage = true;
        }
      });
  }

  hasAccountChanges(): boolean {
    const account = this.account;
    const profile = this.user?.profile || {};

    const fields = [
      'first_name',
      'last_name',
      'company_name',
      'company_email',
      'company_website',
      'company_location'
    ];

    return fields.some(field => {
      const localValue = this.normalize(account[field]);
      const serverValue = this.normalize(profile[field]);
      return localValue !== serverValue;
    });
  }

  updateEmail() {
    if (!this.hasEmailChanges()) return;

    this.loading = true;

    this.userService.updateEmail(this.emailUpdate.old_email, this.emailUpdate.new_email)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: () => {
          this.user.email = this.emailUpdate.new_email
          this.email = this.user.email;

          this.modalTitle = '';
          this.modalMessage = 'Email successfully updated!';
          this.modelType = 'info';
          this.isMessage = true;
        },
        error: (err) => {
          const errors = Object.values(err.error).flat().join(" | ");
          this.modalTitle = '';
          this.modalMessage = errors;
          this.modelType = 'error';
          this.isMessage = true;
        }
      });
  }

  hasEmailChanges(): boolean {
    const account = this.emailUpdate || {};

    const oldEmail = this.normalize(account['old_email']);
    const newEmail = this.normalize(account['new_email']);

    // true samo ako su oba polja NE PRAZNA
    return oldEmail !== '' && newEmail !== '';
  }

  resetPassword() {
    this.showPasswordModal = true;

    // sadržaj emaila u pre-formatu, ali dugme ostaje stilizovano
    this.simulatedEmailContent = `
      <pre style="
        background-color:#f5f5f5;
        padding:15px;
        border-radius:5px;
        font-family: monospace;
        white-space: pre-wrap;
      ">
      Dear user, 

      We have received a request to reset your password. 
      Click the button below to change your password:

      </pre>

      <pre style="
        background-color:#f5f5f5;
        padding:15px;
        border-radius:5px;
        font-family: monospace;
        white-space: pre-wrap;
        margin-top:10px;
      ">
      If you did not request a password change, ignore this message.
      </pre>
        `;
  }

  resetPassword2() {
    if (!this.hasPasswordChanges()) return
    this.loading = true;

    this.userService.changePassword(this.updatePassword.old_password, this.updatePassword.new_password)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: () => {
          this.modalTitle = '';
          this.modalMessage = 'Password changed successfully!';
          this.modelType = 'info';
          this.isMessage = true;
        },
        error: (err) => {
          this.modalTitle = 'An error occurred while changing the password.';
          this.modalMessage = err.message;
          this.modelType = 'error';
          this.isMessage = true;
        }
      });
  }

    getNewPassword(password: string) {
      // sadržaj emaila u pre-formatu, ali dugme ostaje stilizovano
      this.simulatedEmailContent = `
        <pre style="
          background-color:#f5f5f5;
          padding:15px;
          border-radius:5px;
          font-family: monospace;
          white-space: pre-wrap;
        ">
          Dear user, 

          We have received your password reset request.
          Your new password is: ${password}
        </pre>
      `;
      this.showPasswordModal = true;
    }

  resetPassword3() {
    this.loading = true;

    this.userService.generateNewPassword(this.user.username)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: (res: any) => {
          if (res.message === 'success') {
            this.getNewPassword(res.password);
          } else {
            this.modalTitle = 'We were unable to generate the code.';
            this.modalMessage = res.message;
            this.modelType = 'warning';
            this.isMessage = true;
          }
        },
        error: (err: any) => {
          this.modalTitle = 'We were unable to generate the code.';
          this.modalMessage = err.message;
          this.modelType = 'error';
          this.isMessage = true;
        }
      })
  }

  hasPasswordChanges() {
     const account = this.updatePassword || {};

    const oldEmail = this.normalize(account['old_password']);
    const newEmail = this.normalize(account['new_password']);

    // true samo ako su oba polja NE PRAZNA
    return oldEmail !== '' && newEmail !== '';
  }

  closeModal() {
    this.showPasswordModal = false;
  }

  generateToken() {
    if (!this.newTokenName) return;
    this.loading = true;

    this.userService.createPersonalToken(this.newTokenName)
      .pipe(finalize(() => this.loading = false))
      .subscribe({
        next: (token) => {
          this.tokens.push(token); // odmah dodaj novi token u tabelu

          this.modalTitle = '';
          this.modalMessage = 'New token successfully created!';
          this.modelType = 'info';
          this.isMessage = true;
        },
        error: () => {
          this.modalTitle = '';
          this.modalMessage = 'An error occurred while creating the token.';
          this.modelType = 'info';
          this.isMessage = true;
        }
      });
  }

  getTokens() {
    this.isLoadingToken = true;
    this.userService.getPersonalTokens()
    .pipe(finalize(() => this.isLoadingToken = false))
    .subscribe({
      next: (res) => {
        this.tokens = res;
      },
      error: () => this.tokens = [],
    })
  }

  private normalize(value: any): string {
    if (value === null || value === undefined) return '';
    return String(value).trim().toLowerCase();
  }

  onModalOk() {
    this.isMessage = false;
    this.modalTitle = '';
    this.modalMessage = '';
    this.modelType = '';

    // reset password change form
    this.updatePassword.old_password = '';
    this.updatePassword.new_password = '';

    // reset email change form
    this.emailUpdate.old_email = '';
    this.emailUpdate.new_email = '';

    this.newTokenName = '';

    if (this.isRedirect) {
      this.auth.logout();
    }
  }

  isPersonal() {
    if (this.user) {
      return this.userService.getCurrentUser()?.username === this.user.username;
    }
    return false;
  }

  getType() {
    if (this.user) {
      return this.user.role
    }
    return null
  }

  onRoleSelected(row: any) {
    this.selectRole = row.name;
  }

  updateRole() {
    if (!this.selectRole) return;

    this.isRoleLoader = true;

    this.userService.changeRole({username: this.user.username, new_role: this.selectRole})
      .pipe(finalize(() => this.isRoleLoader = false))
      .subscribe({
        next: () => {
          this.modalMessage = 'Role updated';
          this.modelType = 'info';
          this.isMessage = true;
          this.user.role = this.selectRole
        },
        error: () => {
          this.modalMessage = 'Role not updated, server error.';
          this.modelType = 'error';
          this.isMessage = true;
        }
      })  
  }
}
