import { Routes } from '@angular/router';
import { HomeComponent } from './home/home';
import { LoginComponent } from './unauthorize/login/login';
import { RegisterComponent } from './unauthorize/register/register';
import { AuthGuard } from './guards/auth-guard';
import { AuthHomeComponent } from './auth/home/home';

export const routes: Routes = [
    { path: '', component: HomeComponent },
    { path: 'login', component: LoginComponent },
    { path: 'register', component: RegisterComponent },
    { path: 'home', component: AuthHomeComponent, canActivate: [AuthGuard] }
];
