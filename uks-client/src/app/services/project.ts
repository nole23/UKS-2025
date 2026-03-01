import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({providedIn: 'root'})
export class ProjectService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Fetches repositories from the backend with optional search, filters, badges, and pagination.
   *
   * @param query       Search query to match repository name, description, owner, or organization.
   * @param visibility  Filter repositories by visibility: 'all' | 'public' | 'private'. Default is 'all'.
   * @param sorting     Sorting order: 'latest' (default), 'oldest', or 'random'.
   * @param badges      Array of badge filters: 'OFFICIAL', 'VERIFIED', 'SPONSORED'.
   * @param limit       Maximum number of repositories to return (pagination). Default is 20.
   * @param offset      Number of repositories to skip (pagination). Default is 0.
   * 
   * @returns Observable containing paginated repositories:
   * {
   *   count: number,          // total number of matching repositories
   *   next: string | null,    // URL to next page, if any
   *   previous: string | null,// URL to previous page, if any
   *   results: Repository[]   // array of repositories for this page
   * }
   */
  getProjects(
    query: string = '',
    visibility: 'all' | 'public' | 'private' = 'all',
    sorting: 'latest' | 'oldest' | 'random' = 'latest',
    badges: string[] = [],       // ["OFFICIAL", "VERIFIED", "SPONSORED"]
    limit: number = 20,
    offset: number = 0
  ): Observable<any> {
    let params = new HttpParams()
      .set('q', query ?? '')
      .set('visibility', visibility)
      .set('sorting', sorting)
      .set('limit', limit)
      .set('offset', offset);

    // Dodavanje badge filtera
    badges.forEach(badge => {
      params = params.append('badge', badge);
    });

    return this.http.get(this.apiUrl + 'repositories/search/', { params, withCredentials: true });
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

  editVisibilityRepository(repoId: number, visibilityType: string): Observable<any> {
    return this.http.post<any>(this.apiUrl + `repositories/update/visibility`, {repoId: repoId, visibility: visibilityType});
  }
  
  updateBadgeRepository(repoId: number, badge: any): Observable<any> {
    return this.http.patch<any>(this.apiUrl + `repositories/${repoId}/badge/`, {badge: badge});
  }

  deleteRepository(repoId: number): Observable<any> {
    return this.http.delete<any>(this.apiUrl + `repositories/${repoId}/`, {withCredentials: true});
  }

  getProjectStars(repoId: number): Observable<any> {
    return this.http.get<any>(this.apiUrl + `repositories/${repoId}/star`, { withCredentials: true });
  }

  actionToStar(repoId: number, type: boolean): Observable<any> {
    if (type) {
      return this.http.post<any>(this.apiUrl + `repositories/${repoId}/star/`, {}, {withCredentials: true});
    } else {
      return this.http.delete<any>(this.apiUrl + `repositories/${repoId}/star/`, {withCredentials: true});
    }
  }
}
