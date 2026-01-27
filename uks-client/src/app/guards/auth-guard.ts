import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {

  constructor(private router: Router, private auth: AuthService) {}

  canActivate(): boolean {
    const token = this.auth.isLoggedIn(); // ili cookie, zavisi šta koristiš
    if (token) {
      return true; // korisnik je ulogovan
    } else {
      this.router.navigate(['/login']); // nije ulogovan → redirect na login
      return false;
    }
  }
}
