import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, throwError, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { UserService } from './user';

@Injectable({providedIn: 'root'})
export class AuthService {
  private apiUrl = environment.apiUrl;
  
  private tokenKey = 'access';
  private userKey = 'user';
  private roleKey = 'userRole';

  constructor(private router: Router, private http: HttpClient, private userService: UserService) {}

  login(loginForm: any): Observable<any> {
    return this.http.post<any>(this.apiUrl + 'login/', loginForm, { withCredentials: true })
      .pipe(tap((res: any) => {
        localStorage.setItem('access', res.access);
        localStorage.setItem('refresh', res.refresh);
        localStorage.setItem('userRole', res.roles);
        if (res.must_change_password) {
          res.user['password'] = loginForm.password;
          localStorage.setItem('user', JSON.stringify(res.user));
        } else {
          localStorage.setItem('user', JSON.stringify(res.user));
        }
      }))
  }

  changePassword(password: string): Observable<any> {
    const user = this.getLocalstorageByKey(this.userKey)
    if (user === null) {
      return throwError(() => new Error("Password change time has expired."))
    }

    return this.userService.changePassword(user.password, password);
  }

  getLocalstorageByKey(key: string): any {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  }

  getUsername(): any {
    const user = localStorage.getItem(this.userKey);
    return user ? JSON.parse(user) : null;
  }

  getRole(): any {
    const role = localStorage.getItem(this.roleKey);
    return role ?? null;
  }

  logout(): void {
    this.clearAllStorage();
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  clearAllStorage() {
    // Local storage
    localStorage.clear();

    // Session storage
    sessionStorage.clear();

    // Cookies
    document.cookie.split(";").forEach(cookie => {
      const name = cookie.split("=")[0].trim();
      document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
    });
  }
}
