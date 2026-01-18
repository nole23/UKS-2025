import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { RegisterComponent } from './register';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

describe('RegisterComponent', () => {
  let component: RegisterComponent;
  let fixture: ComponentFixture<RegisterComponent>;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RegisterComponent, HttpClientTestingModule, RouterTestingModule.withRoutes([])]
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have initial empty form', () => {
    const formValue = component.registerForm.value;
    // proveravamo samo neka polja koja sigurno postoje
    expect(formValue.username).toBe('');
    expect(formValue.email).toBe('');
    expect(formValue.password).toBe('');
  });

  it('should have isError and isLoading as false initially', () => {
    expect(component.isError).toBeFalse();
    expect(component.isLoading).toBeFalse();
  });

  it('should set isLoading to true when register() is called with valid form', () => {
    // popuni formu validnim vrednostima
    component.registerForm.setValue({
      username: 'testuser',
      email: 'test@test.com',
      password: '123456',
      password2: '123456',    // ako polje postoji
      first_name: 'Test',     // ako polje postoji
      last_name: 'User'       // ako polje postoji
    });

    component.register();
    expect(component.isLoading).toBeTrue();
  });
});
