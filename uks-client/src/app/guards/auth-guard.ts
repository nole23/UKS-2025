import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {

  constructor(private router: Router) {}

  canActivate(): boolean {
    const token = localStorage.getItem('access'); // ili cookie, zavisi šta koristiš
    if (token) {
      return true; // korisnik je ulogovan
    } else {
      this.router.navigate(['/login']); // nije ulogovan → redirect na login
      return false;
    }
  }
}
