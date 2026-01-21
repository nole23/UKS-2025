import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';

@Component({
  selector: 'app-account-settings',
  imports: [FormsModule, CommonModule, RouterModule],
  templateUrl: './account-settings.html',
  styleUrl: './account-settings.scss',
})
export class AccountSettings implements OnInit {

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
  selectedMenu: string | null = null;

  loading = false;       // spinner flag
  message: string = '';  // poruka koja se prikazuje
  error: boolean = false; // da li je poruka greška

  emailMessage: string = '';  // poruka koja se prikazuje
  emailError: boolean = false; // da li je poruka greška

  showPasswordModal: boolean = false; // flag za popup
  simulatedEmailContent: string = ''; // sadržaj emaila

  messagePassword = '';
  errorPassword = false;

  isLoadingToken = false;
  messageToken: string = '';
  errorToken: boolean = false;

  constructor(private auth: AuthService, private userService: UserService) {}

  ngOnInit(): void {
    this.user = this.auth.getUsername()
    this.email = this.user.email;
    this.account = { ...this.user.profile };

    this.getTokens();
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
    this.message = '';    // reset poruke
    this.error = false;

    this.userService.updateProfile(this.account).subscribe({
      next: () => {
        this.loading = false;
        this.message = 'We have successfully completed the update!';
        this.error = false;

        // opcionalno: osveži lokalni account iz response
      },
      error: (err) => {
        this.loading = false;
        this.message = 'An error occurred while updating.';
        this.error = true;
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
    this.emailMessage = '';
    this.emailError = false;

    this.userService.updateEmail(this.emailUpdate.old_email, this.emailUpdate.new_email).subscribe({
      next: (res) => {
        this.loading = false;
        this.emailMessage = 'Email successfully updated!';
        this.emailError = false;

        this.user.email = this.emailUpdate.new_email
        this.email = this.user.email;

        // resetovanje polja
        this.emailUpdate.old_email = '';
        this.emailUpdate.new_email = '';
      },
      error: (err) => {
        this.loading = false;
        this.emailMessage = 'There was an error updating your email.';
        this.emailError = true;
        console.error(err);
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
    if (!this.hasPasswordChanges()) return;

    this.loading = true;
    this.messagePassword = '';
    this.errorPassword = false;

    this.userService.changePassword(this.updatePassword.old_password, this.updatePassword.old_password).subscribe({
      next: () => {
        this.loading = false;
        this.messagePassword = 'Lozinka je uspešno promenjena!';
        this.errorPassword = false;

        // reset forme
        this.updatePassword.old_password = '';
        this.updatePassword.new_password = '';

        setTimeout(() => {
          this.auth.logout(); // automatski logout i redirect na /login
        }, 1500); // 1.5 sekunde delay
      },
      error: (err) => {
        this.loading = false;
        this.messagePassword = 'Došlo je do greške pri promeni lozinke.';
        this.errorPassword = true;
      }
    });
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
    this.messageToken = '';
    this.errorToken = false;

    this.userService.createPersonalToken(this.newTokenName).subscribe({
      next: (token) => {
        this.loading = false;
        this.tokens.push(token); // odmah dodaj novi token u tabelu
        this.messageToken = 'New token successfully created!';
        this.newTokenName = ''; // reset input polja

        setTimeout(() => {
          this.showTokenForm = false;
        }, 1500); // 1.5 sekunde delay
      },
      error: (err) => {
        this.loading = false;
        this.messageToken = 'An error occurred while creating the token.';
        this.errorToken = true;
      }
    });
  }

  getTokens() {
    this.isLoadingToken = true;
    this.userService.getPersonalTokens().subscribe({
      next: (res) => {
        this.tokens = res;
        this.isLoadingToken = false;
      },
      error: (err) => this.tokens = [],
    })
  }

  private normalize(value: any): string {
    if (value === null || value === undefined) return '';
    return String(value).trim().toLowerCase();
  }
}
