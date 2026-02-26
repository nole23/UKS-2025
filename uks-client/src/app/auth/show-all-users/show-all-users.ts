import { Component, effect, inject, signal } from '@angular/core';
import { TableColumn } from '../../helpers/interface/table-column';
import { TableComponent } from '../../helpers/table-component/table-component';
import { UserService } from '../../services/user';
import { Router } from '@angular/router';

@Component({
  selector: 'app-show-all-users',
  imports: [TableComponent],
  templateUrl: './show-all-users.html',
  styleUrl: './show-all-users.scss',
})
export class ShowAllUsers {
  private userService = inject(UserService);
  private router = inject(Router);

  $users: any = [];

  readonly fetch = effect(() => {
    this.userService.getUsers().subscribe((data: any) => {
      this.$users = data
    });
  });

  userColumns: TableColumn[] = [
    { key: 'username', label: 'Username' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role', type: 'badge', classFn: (v) => 'role-badge ' + v },
    // poslednja kolona za akcije
    {
      key: 'actions',
      label: '',
      type: 'buttons',
      buttons: [
        { icon: 'fa fa-eye', title: 'View', class: 'btn-green mr-1', fn: (user: any) => this.viewUser(user) },
        { icon: 'fa fa-edit', title: 'Edit', class: 'btn-transparent', fn: (user: any) => this.editUser(user) }
      ]
    }
  ];

  viewUser(user: any) {
    this.router.navigate(['user', user.id])
  }

  editUser(user: any) {
    this.router.navigate(['account-settings', user.username])
  }
}
