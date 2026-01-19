import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HttpClientModule],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class RegisterComponent {
  registerForm: FormGroup;
  message = '';
  isError = false;
  isLoading = false;
  private apiUrl = environment.apiUrl;

  constructor(private fb: FormBuilder, private http: HttpClient, private router: Router) {
    this.registerForm = this.fb.group({
      username: [''],
      email: [''],
      password: [''],
      password2: [''],
      first_name: [''],
      last_name: ['']
    });
  }

  register() {
    if (this.registerForm.invalid) return;

    this.isLoading = true;
    this.http.post<any>(this.apiUrl + 'register/', this.registerForm.value, { withCredentials: true })
      .subscribe({
        next: (res) => {
          this.message = res.message;
          this.isError = false;
          this.isLoading = false;
          
          let countdown = 3; // 5 sekundi countdown
          this.message = `Registration success! Redirect in ${countdown}s`;

          const interval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
              this.message = `Registration success! Redirect in ${countdown}s`;
            } else {
              clearInterval(interval);
              this.router.navigate(['/login']);
            }
          }, 1000);
        },
        error: (err) => {
          this.message = 'Registration failed!';
          this.isError = true;
          this.isLoading = false;
        }
      });
  }

  goHome() {
    this.router.navigate(['/']); // ili '/home' ako tako zoves home route
  }
}
