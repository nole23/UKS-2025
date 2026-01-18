import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent {
  loginForm: FormGroup;
  message = '';
  isError = false;
  isLoading = false;

  constructor(private fb: FormBuilder, private http: HttpClient, private router: Router) {
    this.loginForm = this.fb.group({
      username: [''],
      password: ['']
    });
  }

  login() {
    if (this.loginForm.invalid) return;

    this.isLoading = true;
    this.http.post<any>('http://localhost:8000/api/login/', this.loginForm.value, { withCredentials: true })
      .subscribe({
        next: (res) => {
          localStorage.setItem('access', res.access);
          localStorage.setItem('refresh', res.refresh);
          this.message = 'Login successful!';
          this.isError = false;
          this.isLoading = false;

          let countdown = 3; // 5 sekundi countdown
          this.message = `Login success! Redirect in ${countdown}s`;

          const interval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
              this.message = `Login success! Redirect in ${countdown}s`;
            } else {
              clearInterval(interval);
              this.router.navigate(['/home']);
            }
          }, 1000);
        },
        error: (err) => {
          this.message = 'Login failed!';
          this.isError = true;
          this.isLoading = false;
        }
      });
  }

  goHome() {
    this.router.navigate(['/']); // ili '/home' ako tako zoves home route
  }
}
