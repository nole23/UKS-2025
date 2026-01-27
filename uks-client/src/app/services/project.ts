import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({providedIn: 'root'})
export class ProjectService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getProjects(query: string = '', visibility: 'all' | 'public' | 'private' = 'all', sortingFilter = 'r'): Observable<any> {
    let params = new HttpParams();
    if(query) params = params.set('q', query);
    
    // šaljemo samo ako nije "all"
    if (visibility !== 'all') {
      params = params.set('visibility', visibility);
    }

    if (sortingFilter != 'r') {
      params = params.set('sorting', sortingFilter);
    }
    return this.http.get(this.apiUrl + 'repositories/search', { params, withCredentials: true });
  }

  /**
   * Kreiraj novi repository
   * @param repository objekat {name, description, visibility, organization_id?}
   */
  createProject(repository: any): Observable<any> {
    return this.http.post<any>(this.apiUrl + 'repositories', repository);
  }

  getProjectTags(repoId: number): Observable<any> {
    return this.http.get<any>(this.apiUrl + `repositories/${repoId}/tags`, { withCredentials: true });
  }

  removeTag(repoId: number, tagId: number): Observable<any> {
    return this.http.delete<any>(this.apiUrl + `repositories/${repoId}/tags/${tagId}/`, { withCredentials: true });
  }

  addTag(repoId: number, tag: any): Observable<any> {
    return this.http.post<any>(this.apiUrl + `repositories/${repoId}/tags/`, tag);
  }

  getCollaborators(repoId: number): Observable<any> {
    return this.http.get<any>(this.apiUrl + `repositories/${repoId}/collaborators/`, { withCredentials: true });
  }

  addCollaborator(repoId: number, userId: number) {
    return this.http.post<any>(this.apiUrl + `repositories/${repoId}/collaborators/`, { user_id: userId, role: 'write' });
  }

  removeCollaborators(repoId: number, userId: number) {
    return this.http.delete<any>(this.apiUrl + `repositories/${repoId}/collaborators/${userId}/`, { withCredentials: true });
  }
}
