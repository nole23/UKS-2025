import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

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
        // opcionalno: možeš ovde dodati logiku za localStorage ili poruku
        console.log('Password updated (simulirano localStorage)');
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
    return this.http.post(url, payload).pipe(
      tap(res => console.log('Novi token kreiran:', res))
    );
  }

  filterUserByText(queryText: string): Observable<any> {
    const url = `${this.apiUrl}profile/search/`;
    let params = new HttpParams();
    if (queryText) {
      params = params.set('q', queryText);
    }

    return this.http.get(url, { params });
  }
}
