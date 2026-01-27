import { Component, OnInit, ViewChild } from '@angular/core';
import { ProjectService } from '../../services/project';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DefautlPrivateRepository } from '../defautl-private-repository/defautl-private-repository';
import { CreateRepository } from '../create-repository/create-repository';
import { RepositoryDetails } from '../repository-details/repository-details';

@Component({
  selector: 'app-home',
  imports: [FormsModule, CommonModule, DefautlPrivateRepository, CreateRepository, RepositoryDetails],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class AuthHomeComponent implements OnInit{
  @ViewChild(CreateRepository) createRepoComp!: CreateRepository;
  projects: any[] = [];
  searchQuery: string = '';
  visibilityFilter: 'all' | 'public' | 'private' = 'all'; // default = sve
  sortingFilter: 'r' | 'l' | 'o' = 'r';
  username: any = '';
  message: string = '';
  isLoading: boolean = false;
  dropdownOpen = false;
  settingsOpen = true;
  typeBody: string = 'home';
  openRepo: any = null;

  constructor(
    private projectService: ProjectService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Uzmi username logovanog korisnika
    this.username = this.authService.getUsername();
    this.loadProjects();
  }

  toggleDropdown() {
    this.dropdownOpen = !this.dropdownOpen;
  }

  loadProjects(): void {
    this.isLoading = true;
    this.projectService.getProjects(this.searchQuery, this.visibilityFilter, this.sortingFilter).subscribe({
      next: (data: any) => {
        this.projects = data;
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

  toggleSettings() {
    this.settingsOpen = !this.settingsOpen;
  }

  openBody(link: string) {
    this.typeBody = link;
  }

  onCreateRepoClose() {
    this.typeBody = 'home';
  }

  onRepoCreated(repo: any) {
    console.log('Repo created:', repo);

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
    console.log(repo);
    this.openRepo = repo;
    this.openBody('open-repo')
  }
}
