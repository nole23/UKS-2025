import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth';

describe('AuthService', () => {
  let service: AuthService;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        { provide: Router, useValue: routerSpy }
      ]
    });
    service = TestBed.inject(AuthService);
    localStorage.clear();
  });

  it('should return username from localStorage', () => {
    localStorage.setItem('user', JSON.stringify('testuser'));
    expect(service.getUsername()).toBe('testuser');
  });

  it('should return null if no username in localStorage', () => {
    expect(service.getUsername()).toBeNull();
  });

  it('should remove token and user and navigate to login on logout', () => {
    localStorage.setItem('access', 'fake-token');
    localStorage.setItem('user', JSON.stringify('testuser'));

    service.logout();

    expect(localStorage.getItem('access')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('isLoggedIn should return true if token exists', () => {
    localStorage.setItem('access', 'fake-token');
    expect(service.isLoggedIn()).toBeTrue();
  });

  it('isLoggedIn should return false if token does not exist', () => {
    expect(service.isLoggedIn()).toBeFalse();
  });
});
