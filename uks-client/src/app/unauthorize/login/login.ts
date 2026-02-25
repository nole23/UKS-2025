import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ModalDialogComponent } from '../../helpers/modal-dialog-component/modal-dialog-component';
import { AuthService } from '../../services/auth';
import { finalize } from 'rxjs';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ModalDialogComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent {
  loginForm: FormGroup;
  isLoading = false;
  showModal = false;
  modalMessage = '';
  modalTitle = '';
  modelType = '';
  redirect = '';  

  constructor(private fb: FormBuilder, private router: Router, private auth: AuthService) {
    this.loginForm = this.fb.group({
      username: [''],
      password: ['']
    });
  }

  login() {
    if (this.loginForm.invalid) return;

    this.isLoading = true;
    this.auth.login(this.loginForm.value)
      .pipe(finalize(() => this.isLoading = false))  
      .subscribe({
        next: (res: any) => {
          if (res.must_change_password) {
            this.modalTitle = 'Change password';
            this.modalMessage = 'You must change your password before continuing';
            this.modelType = "warning";
            this.redirect = '/change-password'
          } else {
            this.modalTitle = 'Successfully';
            this.modalMessage = 'You have successfully logged in!';
            this.modelType = "info";
            this.redirect = '/home'
          }

          this.showModal = true;
        },
        error: (err: any) => {
          this.modalTitle = 'Login failed!'
          this.modalMessage  = err.message;
          this.modelType = "error";
          this.showModal = true;
          this.redirect = '';
        }
      })
  }

  goHome() {
    this.router.navigate(['/']);
  }

  onModalOk() {
    this.showModal = false;
    this.modalMessage = '';
    this.modalTitle = '';
    this.modelType = '';

    if (this.redirect !== '') {
      this.router.navigate([this.redirect])
    }
  }
}
