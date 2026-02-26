import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ProjectService } from '../../services/project';
import { UserService } from '../../services/user';
import { ModalDialogComponent } from '../../helpers/modal-dialog-component/modal-dialog-component';
import { finalize } from 'rxjs';

@Component({
  selector: 'app-repository-details',
  imports: [DatePipe, FormsModule, ModalDialogComponent],
  templateUrl: './repository-details.html',
  styleUrl: './repository-details.scss',
})
export class RepositoryDetails implements OnInit{
  @Input() repository: any;
  @Output() repositoryChange = new EventEmitter<any>();

  activeTab: string = 'general';

  tags: any[] = [];
  lastTag: any = null;
  pulls: any[] = [];
  collaborators: any[] = [];

  searchTerm = '';
  filteredUsers: any[] = [];
  selectedUser: any = null;
  user: any = {}

  modalTitle: string = '';
  modalMessage: string = '';
  modelType: string = '';
  innerDiv: any = null;
  isOpenModal: boolean = false;
  isCancel: boolean = false;

  isVisibilitySpiner: boolean = false;
  isDeleteSpinser: boolean = false;
  globalType: string = '';

  isCollaboratorLoading: boolean = false;
  isTagsLoading: boolean = false;

  constructor(private repo: ProjectService, public userService: UserService) {}

  ngOnInit() {
    this.user = this.userService.getCurrentUser();
    this.loadTags();
    this.loadCollaborators();
  }

  setTab(tab: string) {
    this.activeTab = tab;
  }

  loadTags() {
    this.repo.getProjectTags(this.repository.id)
      .pipe(finalize(() => this.isTagsLoading = true))
      .subscribe({
        next: (res) => {
          this.tags = res;
          if (res.length > 0) {
            this.lastTag = res.reduce((prev: any, current: any) => {
              return new Date(prev.updated_at) > new Date(current.updated_at) ? prev : current;
            });
          }
        },
        error: () => {
        }
      })
  }

  loadCollaborators() {
    this.repo.getCollaborators(this.repository.id)
      .pipe(finalize(() => this.isCollaboratorLoading = true))
      .subscribe({
        next: (res: any) => {
          this.collaborators = res;
        },
        error: () => {}
      })
  }

  onSearchUser() {
    if (this.searchTerm.length < 2) {
      this.filteredUsers = [];
      return;
    }

    this.userService.filterUserByText(this.searchTerm).subscribe({
      next: (res) => {
        this.filteredUsers = res;
      },
      error: () => {
      }
    })
  }

  selectUser(user: any) {
    this.selectedUser = user;
    this.filteredUsers = [];

  }

  addCollaborator() {
    this.repo.addCollaborator(this.repository.id, this.selectedUser.id).subscribe({
      next: (res: any) => {
        this.collaborators.unshift(this.selectedUser)
      }
    })
  }

  removeTag(tag: any) {
    this.repo.removeTag(this.repository.id, tag.id).subscribe({
      next: () => {
        const index = this.tags.findIndex(t => t.id === tag.id);
        if (index > -1) {
          this.tags.splice(index, 1); // ukloni 1 element na tom indexu
        }
      },
      error: () => {
      }
    })
  }

  addTag() {
    const tag = {
      name: `latest_${this.generateRandomString(4)}`,
      digest: "sha256:abcd1234",
      compressed_size_mb: this.getRandomNumber(),
      os_arch: "linux/amd64"
    }
    this.repo.addTag(this.repository.id, tag).subscribe({
      next: (res: any) => {
        this.tags.unshift(res);
      },
      error: () => {
      }
    })
  }

  generateRandomString(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let result = '';
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * chars.length);
      result += chars[randomIndex];
    }
    return result;
  }

  private getRandomNumber(): number {
    const min = 1;
    const max = 200;
    const num = Math.random() * (max - min) + min; // random između 1 i 200
    return parseFloat(num.toFixed(2)); // zaokruži na 2 decimale
  }

  removeCollaborators(collaborator: any) {
    this.repo.removeCollaborators(this.repository.id, collaborator.id).subscribe({
      next: () => {
        const index = this.collaborators.findIndex(t => t.id === collaborator.id);
        if (index > -1) {
          this.collaborators.splice(index, 1); // ukloni 1 element na tom indexu
        }
      }
    })
  }

  isOwner() {
    return this.isRealOwnre || this.collaborators.some(c => c.username === this.user.username);
  }

  isRealOwnre() {
    return this.repository.owner_username === this.user.username
  }

  isDeleteDisabled() {
    return !(this.userService.isSuperAdmin() || this.isRealOwnre());
  }

  getTypeVisibility() {
    return this.repository.visibility === "public" ? "private" : "public"
  }

  openModal(type: string) {
    this.globalType = type;
    if (type === 'visibility') {
      this.modalTitle = 'Visibility settings';
      this.modalMessage = `Change '${this.repository.name}' repository to ${this.getTypeVisibility()}. `;
      this.modelType = '';
      this.isOpenModal = true;
      this.isCancel = true;
    }

    if (type === 'delete') {
      this.modalTitle = 'Delete repository';
      this.modalMessage = '';
      this.innerDiv = `
        <span>
          This deletes the repository, all the tags it contains,
        </span>
        <br>
        <span>
          and its build settings. This cannot be undone.
        </span>
      `
      this.modelType = '';
      this.isOpenModal = true;
      this.isCancel = true;
    }
  }

  onModalOk() {
    this.closeModal();
    if (this.globalType === 'visibility') {
      this.isVisibilitySpiner = true;

      this.repo.editVisibilityRepository(this.repository.id, this.getTypeVisibility())
        .pipe(finalize(() => {
          this.isVisibilitySpiner = false;
          this.globalType = '';
        }))  
        .subscribe({
          next: () => {
            this.modalTitle = '';
            this.modalMessage = `Visibility settings changed to ${this.getTypeVisibility()}`;
            this.modelType = 'info';
            this.isOpenModal = true;

            this.repositoryChange.emit('update')
          },
          error: () => {
            this.modalTitle = '';
            this.modalMessage = `Visibility settings not changed`;
            this.modelType = 'error';
            this.isOpenModal = true;
          }
        })
    }

    if (this.globalType === 'delete') {
      this.isDeleteSpinser = true;

      this.repo.deleteRepository(this.repository.id)
        .pipe(finalize(() => {
          this.isDeleteSpinser = false;
          this.globalType = '';
        }))
        .subscribe({
          next: () => {
            this.modalTitle = '';
            this.modalMessage = `${this.repository.name} repository has deleted`;
            this.modelType = 'info';
            this.isOpenModal = true;

            this.repositoryChange.emit('delete')
          },
          error: () => {
            this.modalTitle = '';
            this.modalMessage = `Repository cannot be deleted.`;
            this.modelType = 'error';
            this.isOpenModal = true;
          }
        })
    }
  }

  onModalCancle() {
    this.closeModal();
    this.globalType = '';
  }

  private closeModal() {
    this.modalTitle = '';
    this.modalMessage = '';
    this.modelType = '';
    this.isOpenModal = false;
    this.innerDiv = null;
    this.isCancel = false;
  }
}
