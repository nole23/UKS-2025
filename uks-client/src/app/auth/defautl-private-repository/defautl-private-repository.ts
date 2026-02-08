import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth';
import { FormsModule } from '@angular/forms';
import { UserService } from '../../services/user';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-defautl-private-repository',
  imports: [FormsModule, CommonModule],
  templateUrl: './defautl-private-repository.html',
  styleUrl: './defautl-private-repository.scss',
})
export class DefautlPrivateRepository implements OnInit {
  user: any = null;
  isSpiner: boolean = false;
  message: string = '';  // poruka koja se prikazuje
  error: boolean = false; // da li je poruka greška
  isDisabledBtn: boolean = false;

  account: any = {
    first_name: "",
    last_name: "",
    company_name: "",
    company_email: "",
    company_website: "",
    company_location: "",
    default_repository: "",
  };

  constructor(private authService: AuthService, private userService: UserService) {}
  
  ngOnInit(): void {
    this.getUser();
    this.isChange();
  }

  updateProfile() {
    if (!this.hasAccountChanges()) { 
      alert('The model has not changed.')
      return
    }

    this.isSpiner = true;

    this.userService.updatePropertyOfRepository(this.account).subscribe({
      next: (res: any) => {
        this.message = "Uspjesno azuriran model"
        this.getUser();
        this.isDisabledBtn = false;
        this.isSpiner = false;
      },
      error: () => {
        this.error = false;
        this.message = "Nismo mogli da sacuvamo izmjenu."
        this.isSpiner = false;
      }
    })
  }

  hasAccountChanges(): boolean {
    const account = this.account;
    const profile = this.user?.profile || {};

    const fields = [
      'first_name',
      'last_name',
      'company_name',
      'company_email',
      'company_website',
      'company_location',
      'default_repository'
    ];

    return fields.some(field => {
      const localValue = this.normalize(account[field]);
      const serverValue = this.normalize(profile[field]);
      return localValue !== serverValue;
    });
  }

  private normalize(value: any): string {
    if (value === null || value === undefined) return '';
    return String(value).trim().toLowerCase();
  }

  isChange() {
    this.isDisabledBtn = this.hasAccountChanges();
    console.log(this.isDisabledBtn)
  }

  getUser() {
    this.user = this.authService.getUsername();
    this.account = { ...this.user.profile };
  }
}
