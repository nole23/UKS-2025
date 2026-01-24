import { TestBed, ComponentFixture } from '@angular/core/testing';
import { AuthHomeComponent } from './home';
import { ProjectService } from '../../services/project';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { of, throwError } from 'rxjs';
import { HttpClientTestingModule } from '@angular/common/http/testing'; // <-- dodaj ovo

describe('AuthHomeComponent (standalone)', () => {
  let component: AuthHomeComponent;
  let fixture: ComponentFixture<AuthHomeComponent>;
  let mockProjectService: any;
  let mockAuthService: any;
  let mockRouter: any;

  beforeEach(async () => {
    mockProjectService = { getProjects: jasmine.createSpy('getProjects') };
    mockAuthService = { getUsername: jasmine.createSpy('getUsername'), logout: jasmine.createSpy('logout') };
    mockRouter = { navigate: jasmine.createSpy('navigate') };

    await TestBed.configureTestingModule({
      imports: [
        AuthHomeComponent,
        FormsModule,
        CommonModule,
        HttpClientTestingModule // <-- ovo omogućava HttpClient injection
      ],
      providers: [
        { provide: ProjectService, useValue: mockProjectService },
        { provide: AuthService, useValue: mockAuthService },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AuthHomeComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('ngOnInit should set username and load projects', () => {
    const fakeUser = 'testuser';
    mockAuthService.getUsername.and.returnValue(fakeUser);
    mockProjectService.getProjects.and.returnValue(of([]));

    component.ngOnInit();

    expect(component.username).toEqual(fakeUser);
    expect(mockProjectService.getProjects).toHaveBeenCalledWith('', 'all', 'r');
  });

  it('loadProjects should populate projects on success', () => {
    const projects = [{ name: 'Repo1' }, { name: 'Repo2' }];
    mockProjectService.getProjects.and.returnValue(of(projects));

    component.loadProjects();

    expect(component.projects).toEqual(projects);
    expect(component.isLoading).toBeFalse();
  });

  it('loadProjects should handle error', () => {
    mockProjectService.getProjects.and.returnValue(throwError(() => new Error('fail')));

    component.loadProjects();

    expect(component.message).toBe('Greška pri učitavanju projekata');
    expect(component.isLoading).toBeFalse();
  });

  it('search should call loadProjects', () => {
    spyOn(component, 'loadProjects');
    component.search();
    expect(component.loadProjects).toHaveBeenCalled();
  });

  it('logout should call authService.logout and navigate', () => {
    component.logout();
    expect(mockAuthService.logout).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('openNewProjectModal should call alert', () => {
    spyOn(window, 'alert');
    component.openNewProjectModal();
    expect(window.alert).toHaveBeenCalledWith('Ovo bi otvorilo modal za kreiranje novog projekta');
  });
});
