import { Component, OnInit } from '@angular/core';
import { ProjectService } from '../../services/project';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-home',
  imports: [FormsModule, CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class AuthHomeComponent implements OnInit{
  projects: any[] = [];
  searchQuery: string = '';
  username: any = '';
  message: string = '';
  isLoading: boolean = false;
  dropdownOpen = false;

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
    this.projectService.getProjects(this.searchQuery).subscribe({
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
}
