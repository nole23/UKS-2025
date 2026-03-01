import { TestBed, ComponentFixture } from '@angular/core/testing';
import { AuthHomeComponent } from './home';
import { ProjectService } from '../../services/project';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { of, throwError } from 'rxjs';
import { HttpClientTestingModule } from '@angular/common/http/testing'; // <-- dodaj ovo
import { UserService } from '../../services/user';

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

  it('loadProjects should populate projects on success', () => {
    const projects = [{ name: 'Repo1' }, { name: 'Repo2' }];
    mockProjectService.getProjects.and.returnValue(of({ results: projects }));

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

  it('ngOnInit should load user and projects', () => {
    spyOn(component, 'loadProjects');
    const userService = TestBed.inject(UserService);

    spyOn(userService, 'getCurrentUser').and.returnValue('user1');
    spyOn(userService, 'getRole').and.returnValue('admin');

    component.ngOnInit();

    expect(component.username).toBe('user1');
    expect(component.userRole).toBe('admin');
    expect(component.loadProjects).toHaveBeenCalled();
  });

  it('should toggle dropdown', () => {
    component.dropdownOpen = false;
    component.toggleDropdown();
    expect(component.dropdownOpen).toBeTrue();
  });

  it('should open only selected panel', () => {
    component.openPanel('analytics');

    expect(component.analitycsPage).toBeTrue();
    expect(component.settingsOpen).toBeFalse();
    expect(component.administrationPage).toBeFalse();
  });

  it('should add badge when checked', () => {
    spyOn(component, 'loadProjects');

    component.onBadgeChange({
      target: { value: 'OFFICIAL', checked: true }
    });

    expect(component.selectedBadges).toContain('OFFICIAL');
    expect(component.loadProjects).toHaveBeenCalled();
  });

  it('should remove badge when unchecked', () => {
    component.selectedBadges = ['OFFICIAL'];
    spyOn(component, 'loadProjects');

    component.onBadgeChange({
      target: { value: 'OFFICIAL', checked: false }
    });

    expect(component.selectedBadges).not.toContain('OFFICIAL');
  });

  it('should open repository', () => {
    const repo = { id: 1 };
    component.openRepository(repo);

    expect(component.openRepo).toBe(repo);
    expect(component.typeBody).toBe('open-repo');
  });

  it('onRepoCreated success', () => {
    component.createRepoComp = {
      stopLoading: jasmine.createSpy(),
      errorMessage: jasmine.createSpy()
    } as any;

    spyOn(component, 'loadProjects');

    mockProjectService.createProject = jasmine.createSpy()
      .and.returnValue(of({}));

    component.onRepoCreated({});

    expect(component.createRepoComp.stopLoading).toHaveBeenCalled();
    expect(component.loadProjects).toHaveBeenCalled();
    expect(component.typeBody).toBe('home');
  });

  it('onRepoCreated error', () => {
    component.createRepoComp = {
      stopLoading: jasmine.createSpy(),
      errorMessage: jasmine.createSpy()
    } as any;

    mockProjectService.createProject = jasmine.createSpy()
      .and.returnValue(throwError(() => new Error()));

    component.onRepoCreated({});

    expect(component.createRepoComp.errorMessage).toHaveBeenCalled();
  });
});
