import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../services/auth';
import { ModalDialogComponent } from '../../../helpers/modal-dialog-component/modal-dialog-component';
import { finalize } from 'rxjs';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ModalDialogComponent],
  templateUrl: './change-password.html',
  styleUrl: './change-password.scss',
})
export class ChangePassword {
  passwordChangeForm: FormGroup;
  isLoading: boolean = false;
  isMessage: boolean = false;
  isError: boolean = false;
  isWarning: boolean = false;
  message: any = '';

  showModal = false;
  modalMessage = '';
  modalTitle = '';
  modelType = '';
  redirect = '';

  constructor(private fb: FormBuilder, private auth: AuthService, private router: Router) {
    this.passwordChangeForm = this.fb.group({
      password: ['', [Validators.required, Validators.pattern(/^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).+$/)]],
      passwordAgain: ['', Validators.required]
    },
    {
      validators: this.passwordMatchValidator,
      updateOn: 'change'
    });
  }

  private passwordMatchValidator(form: AbstractControl) {
    const pass = form.get('password')?.value;
    const confirm = form.get('passwordAgain')?.value;

    return pass === confirm ? null : { passwordMismatch: true };
  }

  goToLoginPage() {
    this.router.navigate(['login'])
  }

  getMismatch() {
    return !this.passwordChangeForm.hasError('passwordMismatch');
  }

  changePassword() {
    this.isLoading = true;
    if (this.passwordChangeForm.invalid) {
      this.isMessage = true;
      this.isWarning = true;
      this.message = 'Password must contain one uppercase letter, one number and one special character.'
      this.isLoading = false;
      return;
    }

    this.isMessage = false;
    this.isWarning = false;
    this.message = ''

    this.auth.changePassword(this.passwordChangeForm.get('password')?.value)
      .pipe(finalize(() => this.isLoading = false))  
      .subscribe({
        next: (res: any) =>  {
          if (res.message === 'Password changed successfully') {
            this.showModal = true;
            this.modalMessage = 'Password successfully updated';
            this.modalTitle = '';
            this.modelType = 'info';
            this.redirect = '/login'
          }
        },
        error: (err: any) => {
          this.showModal = true;
          this.modalMessage = err.message;
          this.modelType = 'error';
          this.redirect = '/change-password'
        }
      })
  }

  onModalOk() {
    this.showModal = false;
    this.modalMessage = '';
    this.modalTitle = '';
    this.modelType = '';

    if (this.redirect !== '') {
      if (this.redirect === '/login') {
        this.auth.logout();
      }
      this.router.navigate([this.redirect])
    }
  }
}
