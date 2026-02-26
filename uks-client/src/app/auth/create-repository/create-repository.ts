import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { UserService } from '../../services/user';

@Component({
  selector: 'app-create-repository',
  imports: [FormsModule],
  templateUrl: './create-repository.html',
  styleUrl: './create-repository.scss',
})
export class CreateRepository {
  @Output() close = new EventEmitter<void>();
  @Output() created = new EventEmitter<any>();
  
  loading: boolean = false;
  message: any = null;

  repository: any = {
    name: '',
    description: '',
    visibility: '',
    organization_id: '',
    official: ''
  }

  constructor(public userService: UserService) {}

  cancel() {
    this.close.emit();
  }

  create() {
    this.loading = true;
    this.created.emit(this.repository); // 👉 javi parentu
  }

  hasAccountChanges(): boolean {
    return !this.normalize(this.repository.name)
      || !this.normalize(this.repository.visibility)
      || !this.normalize(this.repository.description);
  }

  private normalize(value: any): string {
    if (value === null || value === undefined) return '';
    return String(value).trim().toLowerCase();
  }

  stopLoading() {
    this.loading = false;
  }

  errorMessage() {
    this.stopLoading();
    this.message = 'Failed to save repo. Try again.'
  }
}
