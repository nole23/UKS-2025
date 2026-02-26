// import { TestBed } from '@angular/core/testing';
// import { ProjectService } from './project';
// import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

// describe('ProjectService', () => {
//   let service: ProjectService;
//   let httpMock: HttpTestingController;

//   beforeEach(() => {
//     TestBed.configureTestingModule({
//       imports: [HttpClientTestingModule],
//       providers: [ProjectService]
//     });

//     service = TestBed.inject(ProjectService);
//     httpMock = TestBed.inject(HttpTestingController);
//   });

//   afterEach(() => {
//     httpMock.verify(); // Proverava da nema otvorenih HTTP zahteva
//   });

//   it('should be created', () => {
//     expect(service).toBeTruthy();
//   });

//   it('should call API without query', () => {
//     service.getProjects().subscribe();

//     const req = httpMock.expectOne('http://localhost:8000/api/repositories/search');
//     expect(req.request.method).toBe('GET');
//     expect(req.request.params.keys().length).toBe(0); // nema query param
//     expect(req.request.withCredentials).toBeTrue();
//     req.flush([]); // simuliramo prazan odgovor
//   });

//   it('should call API with query', () => {
//     const query = 'test';
//     service.getProjects(query).subscribe();

//     const req = httpMock.expectOne((r) => r.url === 'http://localhost:8000/api/repositories/search' && r.params.get('q') === query);
//     expect(req.request.method).toBe('GET');
//     expect(req.request.params.get('q')).toBe(query);
//     expect(req.request.withCredentials).toBeTrue();
//     req.flush([{ name: 'Repo1' }, { name: 'Repo2' }]); // simuliramo odgovor
//   });

//   it('should return projects on success', () => {
//     const mockProjects = [{ name: 'Repo1' }, { name: 'Repo2' }];

//     service.getProjects().subscribe((projects) => {
//       expect(projects.length).toBe(2);
//       expect(projects).toEqual(mockProjects);
//     });

//     const req = httpMock.expectOne('http://localhost:8000/api/repositories/search');
//     req.flush(mockProjects);
//   });

//   it('should handle error', () => {
//     const errorMsg = 'simulated network error';
//     service.getProjects().subscribe({
//       next: () => fail('should have failed'),
//       error: (error) => {
//         expect(error.statusText).toBe('Bad Request');
//       }
//     });

//     const req = httpMock.expectOne('http://localhost:8000/api/repositories/search');
//     req.flush(errorMsg, { status: 400, statusText: 'Bad Request' });
//   });
// });
