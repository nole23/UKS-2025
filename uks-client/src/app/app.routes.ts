import { Routes } from '@angular/router';
import { HomeComponent } from './home/home';
import { LoginComponent } from './unauthorize/login/login';
import { RegisterComponent } from './unauthorize/register/register';
import { AuthGuard } from './guards/auth-guard';
import { AuthHomeComponent } from './auth/home/home';
import { GuestGuard } from './guards/guest-guard';
import { AccountSettings } from './auth/account-settings/account-settings';
import { DefautlPrivateRepository } from './auth/defautl-private-repository/defautl-private-repository';

export const routes: Routes = [
    { path: '', component: HomeComponent, canActivate: [GuestGuard] },
    { path: 'login', component: LoginComponent, canActivate: [GuestGuard] },
    { path: 'register', component: RegisterComponent, canActivate: [GuestGuard] },
    { path: 'home', component: AuthHomeComponent, canActivate: [AuthGuard] },
    { path: 'account-settings', component: AccountSettings, canActivate: [AuthGuard] },
    { path: 'settings/default-private', component: DefautlPrivateRepository, canActivate: [AuthGuard] },
];
