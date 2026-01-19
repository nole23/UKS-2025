import { HttpRequest, HttpEvent } from '@angular/common/http';
import { of } from 'rxjs';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let next: jasmine.Spy;

  beforeEach(() => {
    next = jasmine.createSpy('next').and.callFake((req: HttpRequest<any>) => of({} as HttpEvent<any>));
    localStorage.clear();
  });

  it('should add Authorization header and withCredentials when token exists', (done) => {
    localStorage.setItem('access', 'fake-token');
    const req = new HttpRequest('GET', '/test');

    authInterceptor(req, next).subscribe(() => {
      expect(next).toHaveBeenCalled();
      const calledReq = next.calls.mostRecent().args[0] as HttpRequest<any>;
      expect(calledReq.headers.get('Authorization')).toBe('Bearer fake-token');
      expect(calledReq.withCredentials).toBeTrue();
      done();
    });
  });

  it('should not modify request when token does not exist', (done) => {
    const req = new HttpRequest('GET', '/test');

    authInterceptor(req, next).subscribe(() => {
      expect(next).toHaveBeenCalled();
      const calledReq = next.calls.mostRecent().args[0] as HttpRequest<any>;
      expect(calledReq.headers.has('Authorization')).toBeFalse();
      expect(calledReq.withCredentials).toBeFalse();
      done();
    });
  });
});
