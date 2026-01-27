import { DatePipe } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ProjectService } from '../../services/project';
import { UserService } from '../../services/user';

@Component({
  selector: 'app-repository-details',
  imports: [DatePipe, FormsModule],
  templateUrl: './repository-details.html',
  styleUrl: './repository-details.scss',
})
export class RepositoryDetails implements OnInit{
  @Input() repository: any;

  activeTab: string = 'general';

  tags: any[] = [];
  lastTag: any = null;
  pulls: any[] = [];
  collaborators: any[] = [];

  users = [
    { username: 'nole' },
    { username: 'admin' },
    { username: 'novica' },
    { username: 'tester' }
  ];

  searchTerm = '';
  filteredUsers: any[] = [];
  selectedUser: any = null;

  constructor(private repo: ProjectService, private userService: UserService) {}

  ngOnInit() {
    this.loadTags();
  }

  setTab(tab: string) {
    this.activeTab = tab;

    if (tab === 'collaborators') this.loadCollaborators();
  }

  loadTags() {
    this.repo.getProjectTags(this.repository.id).subscribe({
      next: (res) => {
        this.tags = res;
        if (res.length > 0) {
          this.lastTag = res.reduce((prev: any, current: any) => {
            return new Date(prev.updated_at) > new Date(current.updated_at) ? prev : current;
          });
        }
      },
      error: (error) => {
        console.log(error)
      }
    })
  }

  loadCollaborators() {
    this.repo.getCollaborators(this.repository.id).subscribe({
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
      error: (err) => {
        console.log(err)
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
      error: (err: any) => {
        console.log(err)
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
}
