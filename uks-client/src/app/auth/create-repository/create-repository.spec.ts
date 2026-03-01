import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CreateRepository } from './create-repository';
import { UserService } from '../../services/user';

describe('CreateRepository Component', () => {
  let component: CreateRepository;
  let fixture: ComponentFixture<CreateRepository>;
  let userServiceMock: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    userServiceMock = jasmine.createSpyObj('UserService', [
        'isAdminOrSuperadmin',
        'getOrganizations'
    ]);

    userServiceMock.getOrganizations.and.returnValue([]);

    await TestBed.configureTestingModule({
        imports: [CreateRepository],
        providers: [
        { provide: UserService, useValue: userServiceMock }
        ]
    }).compileComponents();

    fixture = TestBed.createComponent(CreateRepository);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // =========================
  // EVENT EMITTER — CANCEL
  // =========================
  it('should emit close event on cancel', () => {
    spyOn(component.close, 'emit');

    component.cancel();

    expect(component.close.emit).toHaveBeenCalled();
  });

  // =========================
  // CREATE — NON ADMIN
  // =========================
  it('should force badge NONE for normal user', () => {
    userServiceMock.isAdminOrSuperadmin.and.returnValue(false);
    spyOn(component.created, 'emit');

    component.repository.badge = 'OFFICIAL';
    component.repository.official = true;

    component.create();

    expect(component.loading).toBeTrue();
    expect(component.repository.badge).toBe('NONE');
    expect(component.repository.official).toBeFalse();
    expect(component.created.emit).toHaveBeenCalledWith(component.repository);
  });

  // =========================
  // CREATE — ADMIN
  // =========================
  it('should not override badge for admin', () => {
    userServiceMock.isAdminOrSuperadmin.and.returnValue(true);
    spyOn(component.created, 'emit');

    component.repository.badge = 'OFFICIAL';

    component.create();

    expect(component.repository.badge).toBe('OFFICIAL');
    expect(component.created.emit).toHaveBeenCalled();
  });

  // =========================
  // VALIDATION
  // =========================
  it('should return true if required fields missing', () => {
    component.repository.name = '';
    component.repository.visibility = '';
    component.repository.description = '';

    expect(component.hasAccountChanges()).toBeTrue();
  });

  it('should return false if fields filled', () => {
    component.repository.name = 'Repo';
    component.repository.visibility = 'public';
    component.repository.description = 'desc';

    expect(component.hasAccountChanges()).toBeFalse();
  });

  it('should trim and normalize values', () => {
    component.repository.name = '   ';
    component.repository.visibility = 'public';
    component.repository.description = 'desc';

    expect(component.hasAccountChanges()).toBeTrue();
  });

  // =========================
  // LOADING STATE
  // =========================
  it('should stop loading', () => {
    component.loading = true;

    component.stopLoading();

    expect(component.loading).toBeFalse();
  });

  // =========================
  // ERROR HANDLER
  // =========================
  it('should set error message and stop loading', () => {
    component.loading = true;

    component.errorMessage();

    expect(component.loading).toBeFalse();
    expect(component.message).toBe('Failed to save repo. Try again.');
  });

});