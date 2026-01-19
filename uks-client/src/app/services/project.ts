import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({providedIn: 'root'})
export class ProjectService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getProjects(query: string = '', ): Observable<any> {
    let params = new HttpParams();
    if(query) params = params.set('q', query);
    return this.http.get(this.apiUrl + 'repositories/search', { params, withCredentials: true });
  }
}
