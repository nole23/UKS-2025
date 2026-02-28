import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BrowserCache } from './browser-cache';
import { environment } from '../../environments/environment';
import { UserService } from './user';

describe('UserService', () => {
  let service: UserService;
  let httpMock: HttpTestingController;
  let mockCache: jasmine.SpyObj<BrowserCache>;

  const api = environment.apiUrl;

  beforeEach(() => {
    mockCache = jasmine.createSpyObj('BrowserCache', ['get', 'set', 'remove']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        UserService,
        { provide: BrowserCache, useValue: mockCache }
      ]
    });

    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  // -----------------------
  // UPDATE PROFILE
  // -----------------------
  it('should update profile and localStorage', () => {
    const mockUser = { profile: { name: 'Old' } };
    localStorage.setItem('user', JSON.stringify(mockUser));

    service.updateProfile({ name: 'New' }).subscribe();

    const req = httpMock.expectOne(`${api}profile/update/`);
    expect(req.request.method).toBe('PUT');

    req.flush({ name: 'New' });

    const updated = JSON.parse(localStorage.getItem('user')!);
    expect(updated.profile.name).toBe('New');
  });

  // -----------------------
  // UPDATE EMAIL
  // -----------------------
  it('should update email and localStorage', () => {
    const mockUser = { email: 'old@mail.com', profile: {} };
    localStorage.setItem('user', JSON.stringify(mockUser));

    service.updateEmail('old@mail.com', 'new@mail.com').subscribe();

    const req = httpMock.expectOne(`${api}profile/email/`);
    expect(req.request.method).toBe('PATCH');

    req.flush({});

    const updated = JSON.parse(localStorage.getItem('user')!);
    expect(updated.email).toBe('new@mail.com');
    expect(updated.profile.email).toBe('new@mail.com');
  });

  // -----------------------
  // CHANGE PASSWORD
  // -----------------------
  it('should send password change request', () => {
    service.changePassword('old', 'new').subscribe();

    const req = httpMock.expectOne(`${api}profile/password/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body.old_password).toBe('old');
    expect(req.request.body.new_password).toBe('new');

    req.flush({});
  });

  // -----------------------
  // TOKENS
  // -----------------------
  it('should fetch personal tokens', () => {
    const tokens = [{ name: 't1' }];

    service.getPersonalTokens().subscribe(res => {
      expect(res).toEqual(tokens);
    });

    const req = httpMock.expectOne(`${api}personal-tokens/list/`);
    expect(req.request.method).toBe('GET');
    req.flush(tokens);
  });

  it('should create token', () => {
    service.createPersonalToken('abc').subscribe();

    const req = httpMock.expectOne(`${api}personal-tokens/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.name).toBe('abc');

    req.flush({});
  });

  // -----------------------
  // SEARCH USER TEXT
  // -----------------------
  it('should filter user by text', () => {
    service.filterUserByText('john').subscribe();

    const req = httpMock.expectOne(r =>
      r.url === `${api}profile/search/` && r.params.get('q') === 'john'
    );
    expect(req.request.method).toBe('GET');

    req.flush([]);
  });

  // -----------------------
  // USERS LIST
  // -----------------------
  it('should fetch users', () => {
    service.getUsers().subscribe();

    const req = httpMock.expectOne(`${api}profile/users/`);
    expect(req.request.method).toBe('GET');

    req.flush([]);
  });

  it('should fetch roles', () => {
    service.getCurrnetRoles().subscribe();

    const req = httpMock.expectOne(`${api}profile/roles/`);
    expect(req.request.method).toBe('GET');

    req.flush([]);
  });

  it('should fetch user by username', () => {
    service.filterUserByUsername('john').subscribe();

    const req = httpMock.expectOne(`${api}profile/users/john/`);
    expect(req.request.method).toBe('GET');

    req.flush({});
  });

  // -----------------------
  // CHANGE ROLE
  // -----------------------
  it('should update role in localStorage on success', () => {
    service.changeRole({ new_role: 'Admin' }).subscribe();

    const req = httpMock.expectOne(`${api}profile/roles/`);
    expect(req.request.method).toBe('POST');

    req.flush({ status: 'sucessifull' });

    expect(localStorage.getItem('userRole')).toBe('Admin');
  });

  // -----------------------
  // GENERATE PASSWORD
  // -----------------------
  it('should generate password', () => {
    service.generateNewPassword('john').subscribe();

    const req = httpMock.expectOne(`${api}profile/generate-password/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.username).toBe('john');

    req.flush({});
  });

  // -----------------------
  // ROLE HELPERS
  // -----------------------
  it('getRole should return stored role', () => {
    localStorage.setItem('userRole', 'Admin');
    expect(service.getRole()).toBe('Admin');
  });

  it('getCurrentUser should return parsed user', () => {
    const u = { name: 'John' };
    localStorage.setItem('user', JSON.stringify(u));

    expect(service.getCurrentUser()).toEqual(u);
  });

  it('isSuperAdmin true', () => {
    localStorage.setItem('userRole', 'SuperAdmin');
    expect(service.isSuperAdmin()).toBeTrue();
  });

  it('isAdmin true', () => {
    localStorage.setItem('userRole', 'Admin');
    expect(service.isAdmin()).toBeTrue();
  });

  it('isAdminOrSuperadmin true for admin', () => {
    localStorage.setItem('userRole', 'Admin');
    expect(service.isAdminOrSuperadmin()).toBeTrue();
  });

  it('isAdminOrSuperadmin false', () => {
    localStorage.setItem('userRole', 'User');
    expect(service.isAdminOrSuperadmin()).toBeFalse();
  });

  // -----------------------
  // DEFAULT ORGS
  // -----------------------
  it('getOrganizations should return empty array', () => {
    expect(service.getOrganizations()).toEqual([]);
  });
});