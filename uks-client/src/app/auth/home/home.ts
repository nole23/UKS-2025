import { Component, OnInit, ViewChild } from '@angular/core';
import { ProjectService } from '../../services/project';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DefautlPrivateRepository } from '../defautl-private-repository/defautl-private-repository';
import { CreateRepository } from '../create-repository/create-repository';
import { RepositoryDetails } from '../repository-details/repository-details';
import { ShowAllUsers } from '../show-all-users/show-all-users';
import { UserService } from '../../services/user';
import { TableComponent } from '../../helpers/table-component/table-component';
import { TableColumn } from '../../helpers/interface/table-column';

@Component({
  selector: 'app-home',
  imports: [FormsModule, CommonModule, DefautlPrivateRepository, CreateRepository, RepositoryDetails, ShowAllUsers, TableComponent],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class AuthHomeComponent implements OnInit{
  @ViewChild(CreateRepository) createRepoComp!: CreateRepository;
  projects: any[] = [];
  searchQuery: string = '';
  visibilityFilter: 'all' | 'public' | 'private' = 'all'; // default = sve
  sortingFilter: 'latest' | 'oldest' | 'random' = 'latest';
  username: any = '';
  message: string = '';
  isLoading: boolean = false;
  dropdownOpen = false;
  settingsOpen = true;
  administrationPage = false;
  analitycsPage = false;
  typeBody: string = 'home';
  openRepo: any = null;
  userRole: any = '';
  badgeDropdownOpen = false;
  selectedBadges: string[] = [];

  repoColumns: TableColumn[] = [
    { key:'name', label:'Name' },

    { key:'created_at', label:'Last Updated', type:'date' },

    { key:'visibility', label:'Visibility', type:'badge',
      classFn:(v)=>'visibility '+v
    },

    { key:'owner_username', label:'Owner' },

    { key:'organization_name', label:'Organization' },

    { key:'badge', label:'Badge'}
  ]

  rowAction = this.openRepository.bind(this);

  constructor(
    private projectService: ProjectService,
    private authService: AuthService,
    private router: Router,
    public userService: UserService
  ) {}

  ngOnInit(): void {
    // Uzmi username logovanog korisnika
    this.username = this.userService.getCurrentUser();
    this.userRole = this.userService.getRole();
    this.loadProjects();
  }

  toggleDropdown() {
    this.dropdownOpen = !this.dropdownOpen;
  }

  loadProjects(): void {
    this.isLoading = true;
    this.projectService.getProjects(
      this.searchQuery,
      this.visibilityFilter,
      this.sortingFilter,
      this.selectedBadges
    )
      .subscribe({
        next: (data: any) => {
          this.projects = data.results;
          this.isLoading = false;
        },
        error: () => {
          this.message = 'Greška pri učitavanju projekata';
          this.isLoading = false;
        }
      });
  }

  search(): void {
    this.loadProjects();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  openNewProjectModal(): void {
    alert('Ovo bi otvorilo modal za kreiranje novog projekta'); 
    // Kasnije se poveže sa modalom ili reactive form
  }

  openLink(link: string) {
    this.router.navigate(['/' + link]);
  }

  openPanel(panel: 'settings' | 'administration' | 'analytics') {
    // zatvori sve
    this.settingsOpen = false;
    this.administrationPage = false;
    this.analitycsPage = false;

    // otvori samo izabrani panel
    switch (panel) {
      case 'settings':
        this.settingsOpen = true;
        break;
      case 'administration':
        this.administrationPage = true;
        break;
      case 'analytics':
        this.analitycsPage = true;
        break;
    }
  }

  openBody(link: string) {
    this.typeBody = link;
  }

  onCreateRepoClose() {
    this.typeBody = 'home';
  }

  onRepoCreated(repo: any) {
    this.projectService.createProject(repo).subscribe({
      next: (res) => {
        this.createRepoComp.stopLoading(); // ugasi spinner
        this.loadProjects(); // refresuj listu
        this.typeBody = 'home';
      },
      error: (err) => {
        this.createRepoComp.errorMessage();
      }
    });
  }

  openRepository(repo: any) {
    this.openRepo = repo;
    this.openBody('open-repo')
  }

  onRepoChanged(status: string) {
    this.loadProjects();
    this.typeBody = 'home';
  }

  onBadgeChange(event: any) {
    const badge = event.target.value;
    if (event.target.checked) {
      this.selectedBadges.push(badge);
    } else {
      this.selectedBadges = this.selectedBadges.filter(b => b !== badge);
    }
    this.loadProjects(); // refresuj listu
  }

  toggleBadgeDropdown() {
    this.badgeDropdownOpen = !this.badgeDropdownOpen;
  }
}
