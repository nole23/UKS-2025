import { Routes } from '@angular/router';
import { HomeComponent } from './home/home';
import { LoginComponent } from './unauthorize/login/login';
import { RegisterComponent } from './unauthorize/register/register';
import { AuthGuard } from './guards/auth-guard';
import { AuthHomeComponent } from './auth/home/home';
import { GuestGuard } from './guards/guest-guard';
import { AccountSettings } from './auth/account-settings/account-settings';
import { DefautlPrivateRepository } from './auth/defautl-private-repository/defautl-private-repository';
import { ChangePassword } from './unauthorize/login/change-password/change-password';
import { UserProfile } from './auth/user-profile/user-profile';

export const routes: Routes = [
    { path: '', component: HomeComponent, canActivate: [GuestGuard] },
    { path: 'login', component: LoginComponent, canActivate: [GuestGuard] },
    { path: 'register', component: RegisterComponent, canActivate: [GuestGuard] },
    { path: 'change-password', component: ChangePassword, canActivate: [AuthGuard] },
    { path: 'home', component: AuthHomeComponent, canActivate: [AuthGuard] },
    { path: 'account-settings/:username', component: AccountSettings, canActivate: [AuthGuard] },
    { path: 'settings/default-private', component: DefautlPrivateRepository, canActivate: [AuthGuard] },
    { path: 'user/:id', component: UserProfile, canActivate: [AuthGuard] },
];
