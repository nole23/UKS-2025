import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { environment } from '../../environments/environment';
import { ProjectService } from './project';

describe('ProjectService', () => {
  let service: ProjectService;
  let httpMock: HttpTestingController;
  const api = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ProjectService]
    });

    service = TestBed.inject(ProjectService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // =========================
  // GET PROJECTS
  // =========================
  it('should fetch projects with default params', () => {
    service.getProjects().subscribe();

    const req = httpMock.expectOne(r =>
      r.url === api + 'repositories/search/' &&
      r.params.get('q') === '' &&
      r.params.get('visibility') === 'all' &&
      r.params.get('sorting') === 'latest' &&
      r.params.get('limit') === '20' &&
      r.params.get('offset') === '0'
    );

    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();

    req.flush({});
  });

  it('should send search filters and badges', () => {
    service.getProjects('test', 'public', 'oldest', ['OFFICIAL','VERIFIED'], 5, 10).subscribe();

    const req = httpMock.expectOne(r =>
      r.url === api + 'repositories/search/' &&
      r.params.get('q') === 'test' &&
      r.params.getAll('badge')?.length === 2
    );

    expect(req.request.params.get('visibility')).toBe('public');
    expect(req.request.params.get('sorting')).toBe('oldest');
    expect(req.request.params.get('limit')).toBe('5');
    expect(req.request.params.get('offset')).toBe('10');

    req.flush({});
  });

  // =========================
  // CREATE PROJECT
  // =========================
  it('should create project', () => {
    const repo = { name: 'Repo1' };

    service.createProject(repo).subscribe();

    const req = httpMock.expectOne(api + 'repositories');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(repo);

    req.flush({});
  });

  // =========================
  // TAGS
  // =========================
  it('should get project tags', () => {
    service.getProjectTags(5).subscribe();

    const req = httpMock.expectOne(api + 'repositories/5/tags');
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();

    req.flush([]);
  });

  it('should remove tag', () => {
    service.removeTag(5, 9).subscribe();

    const req = httpMock.expectOne(api + 'repositories/5/tags/9/');
    expect(req.request.method).toBe('DELETE');
    expect(req.request.withCredentials).toBeTrue();

    req.flush({});
  });

  it('should add tag', () => {
    service.addTag(5, { name: 'tag' }).subscribe();

    const req = httpMock.expectOne(api + 'repositories/5/tags/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.name).toBe('tag');

    req.flush({});
  });

  // =========================
  // COLLABORATORS
  // =========================
  it('should get collaborators', () => {
    service.getCollaborators(3).subscribe();

    const req = httpMock.expectOne(api + 'repositories/3/collaborators/');
    expect(req.request.method).toBe('GET');
    expect(req.request.withCredentials).toBeTrue();

    req.flush([]);
  });

  it('should add collaborator', () => {
    service.addCollaborator(3, 11).subscribe();

    const req = httpMock.expectOne(api + 'repositories/3/collaborators/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ user_id: 11, role: 'write' });

    req.flush({});
  });

  it('should remove collaborator', () => {
    service.removeCollaborators(3, 11).subscribe();

    const req = httpMock.expectOne(api + 'repositories/3/collaborators/11/');
    expect(req.request.method).toBe('DELETE');
    expect(req.request.withCredentials).toBeTrue();

    req.flush({});
  });

  // =========================
  // VISIBILITY
  // =========================
  it('should change visibility', () => {
    service.editVisibilityRepository(7, 'private').subscribe();

    const req = httpMock.expectOne(api + 'repositories/update/visibility');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      repoId: 7,
      visibility: 'private'
    });

    req.flush({});
  });

  // =========================
  // BADGE UPDATE
  // =========================
  it('should update badge', () => {
    service.updateBadgeRepository(4, 'OFFICIAL').subscribe();

    const req = httpMock.expectOne(api + 'repositories/4/badge/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ badge: 'OFFICIAL' });

    req.flush({});
  });

  // =========================
  // DELETE REPOSITORY
  // =========================
  it('should delete repository', () => {
    service.deleteRepository(99).subscribe();

    const req = httpMock.expectOne(api + 'repositories/99/');
    expect(req.request.method).toBe('DELETE');
    expect(req.request.withCredentials).toBeTrue();

    req.flush({});
  });

});