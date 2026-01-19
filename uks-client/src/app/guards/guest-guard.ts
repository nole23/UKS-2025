// guest-guard.ts
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth';

@Injectable({
  providedIn: 'root',
})
export class GuestGuard implements CanActivate {

  constructor(private router: Router, private auth: AuthService) {}

  canActivate(): boolean {
    if (this.auth.isLoggedIn()) {
      // Ako je korisnik ulogovan → redirect na home
      this.router.navigate(['/home']);
      return false;
    }
    // Ako nije ulogovan → može pristupiti login/register
    return true;
  }
}
