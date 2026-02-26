import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { BrowserCache } from './browser-cache';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private apiUrl = environment.apiUrl;
  private roleKey = 'userRole';
  private userKey = 'user';

  constructor(private http: HttpClient, private bc: BrowserCache) {}

  /**
   * Update user profile
   * @param data - objekat sa poljima koja se update-uju
   * @returns Observable sa odgovorom API-ja
   */
  updateProfile(data: any): Observable<any> {
    const url = `${this.apiUrl}profile/update/`;

    return this.http.put(url, data).pipe(
      tap((response: any) => {
        // Ako postoji user u localStorage, ažuriraj njegove podatke
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          // Pretpostavljamo da API vraća novi profile objekat u response
          user.profile = { ...user.profile, ...response };
          localStorage.setItem('user', JSON.stringify(user));
        }
      })
    );
  }

  /**
   * Update user email
   * @param oldEmail - trenutni email korisnika
   * @param newEmail - novi email
   * @returns Observable sa odgovorom API-ja
   */
  updateEmail(oldEmail: string, newEmail: string): Observable<any> {
    const url = `${this.apiUrl}profile/email/`;
    const payload = { old_email: oldEmail, new_email: newEmail };

    return this.http.patch(url, payload).pipe(
      tap((response: any) => {
        // Ažuriramo localStorage sa novim emailom ako postoji
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          user.email = newEmail;          // ažuriramo glavni email
          if (user.profile) {
            user.profile.email = newEmail; // ako postoji u profilu
          }
          localStorage.setItem('user', JSON.stringify(user));
        }
      })
    );
  }

  /**
   * Change user password
   * @param oldPassword - trenutna lozinka
   * @param newPassword - nova lozinka
   * @returns Observable sa odgovorom API-ja
   */
  changePassword(oldPassword: string, newPassword: string): Observable<any> {
    const url = `${this.apiUrl}profile/password/`;
    const payload = { old_password: oldPassword, new_password: newPassword };

    return this.http.patch(url, payload).pipe(
      tap(() => {
        
      })
    );
  }

  /**
   * List of all tokens
   * @returns all tokens
   */
  getPersonalTokens(): Observable<any[]> {
    const url = `${this.apiUrl}personal-tokens/list/`;
    return this.http.get<any[]>(url);
  }

  /**
   * Create new token
   * @param name - ime tokena
   * @returns 
   */
  createPersonalToken(name: string): Observable<any> {
    const url = `${this.apiUrl}personal-tokens/`;
    const payload = { name };
    return this.http.post(url, payload);
  }

  filterUserByText(queryText: string): Observable<any> {
    const url = `${this.apiUrl}profile/search/`;
    let params = new HttpParams();
    if (queryText) {
      params = params.set('q', queryText);
    }

    return this.http.get(url, { params });
  }

  updatePropertyOfRepository(updateDefaultRepository: any): Observable<any> {
    const url = `${this.apiUrl}profile/update/`;

    return this.http.put(url, updateDefaultRepository).pipe(
      tap((response: any) => {
        // Ako postoji user u localStorage, ažuriraj njegove podatke
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          // Pretpostavljamo da API vraća novi profile objekat u response
          user.profile = { ...user.profile, ...response };
          localStorage.setItem('user', JSON.stringify(user));
        }
      })
    );
  }

  getUsers(): Observable<any> {
    const url = `${this.apiUrl}profile/users/`;
    return this.http.get<any>(url);
  }

  getCurrnetRoles(): Observable<any> {
    const url = `${this.apiUrl}profile/roles/`;
    return this.http.get<any>(url);
  }

  filterUserByUsername(username: string): Observable<any> {
      const url = `${this.apiUrl}profile/users/${username}/`;
      return this.http.get<any>(url);
  }

  changeRole(role: any): Observable<any> {
    const url = `${this.apiUrl}profile/roles/`;
    return this.http.post<any>(url, role).pipe(
      tap((response: any) => {
        if (response.status === 'sucessifull') {
          localStorage.removeItem(this.roleKey);
          localStorage.setItem(this.roleKey, role.new_role)
        }
      })
    )
  }

  generateNewPassword(username: string) {
    const url = `${this.apiUrl}profile/generate-password/`;
    return this.http.post<any>(url, {username: username});
  }

  getRole() {
    const r = localStorage.getItem(this.roleKey);
    if(r) {
      return r.toString();
    };
    return null;
  }

  getCurrentUser() {
    const u = localStorage.getItem(this.userKey);
    if (u) {
      return JSON.parse(u);
    }

    return null;
  }

  isSuperAdmin(): boolean {
    return this.getRole()?.toLowerCase() === 'superadmin';
  }

  isAdmin(): boolean {
    return this.getRole()?.toLowerCase() === 'admin';
  }

  isAdminOrSuperadmin(): boolean {
    return this.isAdmin() || this.isSuperAdmin();
  }
}
