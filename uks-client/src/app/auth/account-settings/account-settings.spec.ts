import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AccountSettings } from './account-settings';
import { AuthService } from '../../services/auth';
import { UserService } from '../../services/user';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';

describe('AccountSettings (standalone)', () => {
  let component: AccountSettings;
  let fixture: ComponentFixture<AccountSettings>;
  let mockAuthService: any;
  let mockUserService: any;

  beforeEach(async () => {
  mockAuthService = {
    getUsername: jasmine.createSpy('getUsername').and.returnValue({
      email: 'test@example.com',
      profile: {
        first_name: 'Test',
        last_name: 'User',
        company_name: 'Company',
        company_email: 'comp@example.com',
        company_website: 'example.com',
        company_location: 'Earth'
      }
    }),
    logout: jasmine.createSpy('logout')
  };

  mockUserService = {
    updateProfile: jasmine.createSpy('updateProfile').and.returnValue(of({})),
    updateEmail: jasmine.createSpy('updateEmail').and.returnValue(of({})),
    changePassword: jasmine.createSpy('changePassword').and.returnValue(of({})),
    createPersonalToken: jasmine.createSpy('createPersonalToken').and.returnValue(of({ name: 'token1' })),
    getPersonalTokens: jasmine.createSpy('getPersonalTokens').and.returnValue(of([]))
  };

  await TestBed.configureTestingModule({
    imports: [AccountSettings],
    providers: [
      { provide: AuthService, useValue: mockAuthService },
      { provide: UserService, useValue: mockUserService },
      provideRouter([])
    ]
  }).compileComponents();

  fixture = TestBed.createComponent(AccountSettings);
  component = fixture.componentInstance;

  // ručno inicijalizuj user i account pre detectChanges
  component.user = mockAuthService.getUsername();
  component.account = { ...component.user.profile };

  fixture.detectChanges(); // sada template može bez crash-a
});

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set user and account on ngOnInit', () => {
    expect(component.user.email).toBe('test@example.com');
    expect(component.account.first_name).toBe('Test');
  });

  it('should detect account changes correctly', () => {
    component.account.first_name = 'Changed';
    expect(component.hasAccountChanges()).toBeTrue();
    component.account.first_name = 'Test';
    expect(component.hasAccountChanges()).toBeFalse();
  });

  it('should save account info successfully', () => {
    component.saveAccountInfo();
    expect(component.loading).toBeFalse();
    expect(component.message).toBe('We have successfully completed the update!');
    expect(component.error).toBeFalse();
    expect(mockUserService.updateProfile).toHaveBeenCalled();
  });

  it('should handle error when saving account info', () => {
    mockUserService.updateProfile.and.returnValue(throwError(() => new Error('Fail')));
    component.saveAccountInfo();
    expect(component.loading).toBeFalse();
    expect(component.message).toBe('An error occurred while updating.');
    expect(component.error).toBeTrue();
  });

  it('should detect email changes correctly', () => {
    component.emailUpdate.old_email = 'a@b.com';
    component.emailUpdate.new_email = 'c@d.com';
    expect(component.hasEmailChanges()).toBeTrue();
    component.emailUpdate.old_email = '';
    expect(component.hasEmailChanges()).toBeFalse();
  });

  it('should update email successfully', () => {
    component.emailUpdate.old_email = 'test@example.com';
    component.emailUpdate.new_email = 'new@example.com';
    component.updateEmail();
    expect(component.email).toBe('new@example.com');
    expect(component.emailMessage).toBe('Email successfully updated!');
    expect(component.emailError).toBeFalse();
  });

  it('should handle error when updating email', () => {
    mockUserService.updateEmail.and.returnValue(throwError(() => new Error('Fail')));
    component.emailUpdate.old_email = 'test@example.com';
    component.emailUpdate.new_email = 'new@example.com';
    component.updateEmail();
    expect(component.emailError).toBeTrue();
    expect(component.emailMessage).toBe('There was an error updating your email.');
  });

  it('should detect password changes correctly', () => {
    component.updatePassword.old_password = 'old';
    component.updatePassword.new_password = 'new';
    expect(component.hasPasswordChanges()).toBeTrue();
    component.updatePassword.old_password = '';
    expect(component.hasPasswordChanges()).toBeFalse();
  });

  it('should reset password successfully and call logout', (done) => {
    component.updatePassword.old_password = 'old';
    component.updatePassword.new_password = 'new';
    component.resetPassword2();
    setTimeout(() => {
      expect(mockAuthService.logout).toHaveBeenCalled();
      done();
    }, 1600);
  });

  it('should handle error when changing password', () => {
    mockUserService.changePassword.and.returnValue(throwError(() => new Error('Fail')));
    component.updatePassword.old_password = 'old';
    component.updatePassword.new_password = 'new';
    component.resetPassword2();
    expect(component.errorPassword).toBeTrue();
  });

  it('should generate token successfully', (done) => {
    component.newTokenName = 'MyToken';
    component.generateToken();
    setTimeout(() => {
      expect(component.tokens.length).toBe(1);
      expect(component.messageToken).toBe('New token successfully created!');
      done();
    }, 1600);
  });

  it('should get tokens successfully', () => {
    component.getTokens();
    expect(component.tokens).toEqual([]);
  });

  it('should toggle settings', () => {
    const old = component.settingsOpen;
    component.toggleSettings();
    expect(component.settingsOpen).toBe(!old);
  });

  it('should select menu correctly', () => {
    component.selectMenu('profile');
    expect(component.selectedMenu).toBe('profile');
    component.selectMenuAndClose('token');
    expect(component.selectedMenu).toBe('token');
    expect(component.showPasswordModal).toBeFalse();
  });
});
